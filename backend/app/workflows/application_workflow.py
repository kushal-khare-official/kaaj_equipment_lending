"""
Hatchet Workflow Implementation for Lender Matching Platform.

This module implements a comprehensive workflow system using Hatchet SDK that:
1. Validates application completeness at each step
2. Runs verification checks (KYC, KYB, Credit, Bank, etc.) in parallel
3. Derives features from application data
4. Matches against lender programs with fit scoring
5. Persists results with full audit trail

The workflow is designed to run incrementally as the user progresses through
the application form, providing real-time feedback and early detection of issues.

Hatchet SDK v0.40+ compatible.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from hatchet_sdk import Hatchet, Context, workflow, step

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.application import Application, MatchRun, MatchResult
from app.models.lender import LenderProgram
from app.services.verification_checks import verification_service
from app.services.document_analysis import document_analysis_service
from app.services.matching import (
    evaluate_application_against_program,
    calculate_assigned_term,
    calculate_interest_rate,
)
from app.services.audit_logger import log_action
from app.services.document_requests import document_request_service
from app.shared.workflow_enums import (
    ApplicationStep,
    CheckType,
    CheckStatus,
    WorkflowStatus,
    RiskLevel,
    CheckResult,
    STEP_CHECKS,
    REQUIRED_CHECKS,
)
from app.shared.enums import ReviewStatus, ApplicationStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Input/Output Schemas
# =============================================================================

class WorkflowInput:
    """Input schema for the application workflow."""
    
    def __init__(self, data: Dict[str, Any]):
        self.application_id: UUID = UUID(data["application_id"])
        self.step: ApplicationStep = ApplicationStep(data["step"])
        self.run_matching: bool = data.get("run_matching", False)


# =============================================================================
# Helper Functions
# =============================================================================

def get_db_session() -> Session:
    """Create a new database session."""
    return SessionLocal()


def load_application(db: Session, application_id: UUID) -> Optional[Application]:
    """Load application with all relationships."""
    return db.query(Application).filter(Application.id == application_id).first()


def build_application_data(application: Application) -> Dict[str, Any]:
    """Build application data dict from ORM model."""
    return {
        "merchant_email": application.merchant_email,
        "business_name": application.business_name,
        "loan_type": application.loan_type,
        "tin": getattr(application, "tin", None),
        "website": getattr(application, "website", None),
        "state": getattr(application, "state", None),
        "account_number": getattr(application, "account_number", None),
        "routing_number": getattr(application, "routing_number", None),
        "guarantors": [
            {
                "is_primary": g.is_primary,
                "first_name": g.first_name,
                "last_name": g.last_name,
                "fico": g.fico,
                "ssn": getattr(g, "ssn", None),
                "address": getattr(g, "address", None),
            }
            for g in application.guarantors
        ] if application.guarantors else [],
        "business_credit": {
            "paynet_score": application.business_credit.paynet_score,
            "revolving_utilization": application.business_credit.revolving_utilization,
        } if application.business_credit else {},
        "equipment": [
            {
                "type": e.type,
                "year": e.year,
                "mileage": e.mileage,
                "titled": e.titled,
                "private_party": e.private_party,
                "hours": e.hours,
            }
            for e in application.equipment
        ] if application.equipment else [],
        "loan_request": {
            "amount": float(application.loan_request.amount) if application.loan_request and application.loan_request.amount else None,
            "term_months": application.loan_request.term_months if application.loan_request else None,
            "down_payment": float(application.loan_request.down_payment) if application.loan_request and application.loan_request.down_payment else None,
        } if application.loan_request else {},
        "documents": [
            {
                "url": doc.uploads[0].url if doc.uploads else None,
                "type": doc.type,
            }
            for doc in application.document_requests
            if doc.uploads
        ] if application.document_requests else [],
    }


def build_check_data(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build the data dict needed for verification checks."""
    data = {
        "business_name": app_data.get("business_name"),
        "tin": app_data.get("tin"),
        "website": app_data.get("website"),
        "state": app_data.get("state"),
        "account_number": app_data.get("account_number"),
        "routing_number": app_data.get("routing_number"),
    }

    # Get primary guarantor info
    guarantors = app_data.get("guarantors", [])
    primary = next((g for g in guarantors if g.get("is_primary")), guarantors[0] if guarantors else {})

    data["first_name"] = primary.get("first_name")
    data["last_name"] = primary.get("last_name")
    data["ssn"] = primary.get("ssn")
    data["address"] = primary.get("address")

    return data


def serialize_check_results(check_results: Dict[str, CheckResult]) -> Dict[str, Any]:
    """Serialize check results for storage."""
    serialized = {}
    for key, result in check_results.items():
        if isinstance(result, CheckResult):
            serialized[key] = {
                "check_type": result.check_type.value,
                "status": result.status.value,
                "vendor": result.vendor,
                "verified": result.verified,
                "score": result.score,
                "risk_level": result.risk_level.value if result.risk_level else None,
                "flags": result.flags,
                "error": result.error,
                "duration_ms": result.duration_ms,
            }
    return serialized


def reconstruct_check_result(data: Dict[str, Any]) -> CheckResult:
    """Reconstruct a CheckResult from serialized data."""
    return CheckResult(
        check_type=CheckType(data.get("check_type", "kyc")),
        status=CheckStatus(data.get("status", "completed")),
        vendor=data.get("vendor"),
        verified=data.get("verified", False),
        score=data.get("score"),
        risk_level=RiskLevel(data["risk_level"]) if data.get("risk_level") else None,
        flags=data.get("flags", []),
        error=data.get("error"),
        duration_ms=data.get("duration_ms"),
    )


# =============================================================================
# Hatchet Workflow Definition
# =============================================================================

@workflow(name="application-workflow", on_events=["application:process"])
class ApplicationWorkflow:
    """
    Main workflow class for application processing.

    This workflow runs different checks based on the application step:

    Step 1 (BUSINESS_SEARCH): No checks, just search
    Step 2 (BUSINESS_DETAILS): KYB, Business Credit, Online Presence, UCC Search
    Step 3 (GUARANTOR_INFO): KYC, Personal Credit Check
    Step 4 (EQUIPMENT_INFO): Feature derivation only
    Step 5 (LOAN_DETAILS): Bank Verification
    Step 6 (DOCUMENTS): Document Analysis, Bank Statement Analysis
    Step 7 (REVIEW): Final lender matching
    Step 8 (SUBMITTED): No checks, final state

    DAG Structure:
        validate → verify → analyze_docs → derive → assess ─┬─► match ────────┬─► persist
                                                            └─► request_docs ──┘
    """

    # =========================================================================
    # Step 1: Validate Application Completeness
    # =========================================================================
    @step(timeout="5s", retries=0)
    async def validate(self, context: Context) -> Dict[str, Any]:
        """
        Validate that required data is present for the current step.

        This is the first step that runs for every workflow execution.
        It checks that the minimum required fields are populated before
        proceeding with verification checks.

        Returns:
            dict with status, errors, warnings, and application_data
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        
        application_id = workflow_input.application_id
        step = workflow_input.step
        
        logger.info(f"[validate] Application {application_id} at step {step}")

        db = get_db_session()
        try:
            application = load_application(db, application_id)
            if not application:
                return {
                    "status": "failed",
                    "errors": [f"Application {application_id} not found"],
                    "warnings": [],
                }

            app_data = build_application_data(application)
            errors = []
            warnings = []

            # Common validation
            if not app_data.get("merchant_email"):
                errors.append("Merchant email is required")

            # Step-specific validation
            if step in [ApplicationStep.BUSINESS_DETAILS, ApplicationStep.GUARANTOR_INFO,
                        ApplicationStep.EQUIPMENT_INFO, ApplicationStep.LOAN_DETAILS,
                        ApplicationStep.DOCUMENTS, ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
                if not app_data.get("business_name"):
                    errors.append("Business name is required")

            if step in [ApplicationStep.GUARANTOR_INFO, ApplicationStep.EQUIPMENT_INFO,
                        ApplicationStep.LOAN_DETAILS, ApplicationStep.DOCUMENTS,
                        ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
                guarantors = app_data.get("guarantors", [])
                if not guarantors:
                    errors.append("At least one guarantor is required")
                else:
                    primary = next((g for g in guarantors if g.get("is_primary")), None)
                    if not primary:
                        errors.append("Primary guarantor must be designated")
                    elif not primary.get("first_name") or not primary.get("last_name"):
                        errors.append("Primary guarantor name is required")

            if step in [ApplicationStep.EQUIPMENT_INFO, ApplicationStep.LOAN_DETAILS,
                        ApplicationStep.DOCUMENTS, ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
                equipment = app_data.get("equipment", [])
                if not equipment:
                    warnings.append("No equipment information provided")

            if step in [ApplicationStep.LOAN_DETAILS, ApplicationStep.DOCUMENTS,
                        ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
                loan_request = app_data.get("loan_request", {})
                if not loan_request.get("amount"):
                    errors.append("Loan amount is required")

            if step in [ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
                if not app_data.get("business_credit", {}).get("paynet_score"):
                    warnings.append("PayNet score not available")

            status = "failed" if errors else "passed"
            if errors:
                logger.warning(f"[validate] Application {application_id} failed: {errors}")
            else:
                logger.info(f"[validate] Application {application_id} passed")

            return {
                "status": status,
                "errors": errors,
                "warnings": warnings,
                "application_data": app_data,
            }
        finally:
            db.close()

    # =========================================================================
    # Step 2: Run Verification Checks in Parallel
    # =========================================================================
    @step(timeout="60s", retries=3, parents=["validate"])
    async def verify(self, context: Context) -> Dict[str, Any]:
        """
        Run verification checks appropriate for the current step.

        Checks are executed in parallel using asyncio.gather for performance.
        Results are aggregated and any failures are tracked.

        Returns:
            dict with check_results, risk_flags, errors, warnings
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        validate_output = context.step_output("validate")

        if validate_output.get("status") == "failed":
            logger.info("[verify] Skipping - validation failed")
            return {
                "check_results": {},
                "risk_flags": [],
                "errors": validate_output.get("errors", []),
                "warnings": validate_output.get("warnings", []),
            }

        current_step = workflow_input.step
        app_data = validate_output.get("application_data", {})
        checks_to_run = STEP_CHECKS.get(current_step, [])

        if not checks_to_run:
            logger.info(f"[verify] No checks for step {current_step}")
            return {
                "check_results": {},
                "risk_flags": [],
                "errors": [],
                "warnings": validate_output.get("warnings", []),
            }

        logger.info(f"[verify] Running {len(checks_to_run)} checks for step {current_step}")

        check_data = build_check_data(app_data)
        check_results = {}
        risk_flags = []
        errors = []
        warnings = list(validate_output.get("warnings", []))

        try:
            results = await verification_service.run_checks_parallel(
                checks=checks_to_run,
                application_data=check_data,
            )

            for check_type, result in results.items():
                if isinstance(result, CheckResult):
                    check_results[check_type] = result
                    risk_flags.extend(result.flags)

                    if result.status == CheckStatus.FAILED:
                        if CheckType(check_type) in REQUIRED_CHECKS:
                            errors.append(f"{check_type} check failed: {result.error}")
                        else:
                            warnings.append(f"{check_type} check failed: {result.error}")

                    if result.status == CheckStatus.NEEDS_REVIEW:
                        warnings.append(f"{check_type} requires manual review")

            logger.info(f"[verify] Completed with {len(risk_flags)} risk flags")

        except Exception as e:
            logger.error(f"[verify] Failed: {str(e)}")
            errors.append(f"Verification checks failed: {str(e)}")

        return {
            "check_results": serialize_check_results(check_results),
            "risk_flags": risk_flags,
            "errors": errors,
            "warnings": warnings,
        }

    # =========================================================================
    # Step 3: Document Analysis (for DOCUMENTS step)
    # =========================================================================
    @step(timeout="120s", retries=2, parents=["verify"])
    async def analyze_docs(self, context: Context) -> Dict[str, Any]:
        """
        Analyze uploaded documents using AI.

        This step only runs during the DOCUMENTS step when documents
        have been uploaded. It performs:
        - Document type verification
        - Data extraction
        - Fraud detection
        - Bank statement analysis

        Returns:
            dict with document_results, risk_flags, warnings
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        validate_output = context.step_output("validate")
        verify_output = context.step_output("verify")

        current_step = workflow_input.step
        
        # Pass through previous results
        result = {
            "document_results": {},
            "risk_flags": list(verify_output.get("risk_flags", [])),
            "warnings": list(verify_output.get("warnings", [])),
        }

        if current_step != ApplicationStep.DOCUMENTS:
            return result

        if validate_output.get("status") == "failed":
            logger.info("[analyze_docs] Skipping - validation failed")
            return result

        app_data = validate_output.get("application_data", {})
        documents = app_data.get("documents", [])
        
        if not documents:
            logger.info("[analyze_docs] No documents to analyze")
            return result

        logger.info(f"[analyze_docs] Analyzing {len(documents)} documents")

        try:
            validation_data = {
                "business_name": app_data.get("business_name"),
                "account_holder": app_data.get("guarantors", [{}])[0].get("first_name"),
            }

            doc_results = await document_analysis_service.analyze_documents_parallel(
                documents=documents,
                validation_data=validation_data,
            )

            for url, doc_result in doc_results.items():
                result["document_results"][f"document_{url}"] = serialize_check_results({url: doc_result}).get(url, {})
                result["risk_flags"].extend(doc_result.flags)

                if doc_result.status == CheckStatus.NEEDS_REVIEW:
                    result["warnings"].append(f"Document requires review: {url}")

            logger.info("[analyze_docs] Complete")

        except Exception as e:
            logger.error(f"[analyze_docs] Failed: {str(e)}")
            result["warnings"].append(f"Document analysis failed: {str(e)}")

        return result

    # =========================================================================
    # Step 4: Derive Application Features
    # =========================================================================
    @step(timeout="10s", retries=1, parents=["analyze_docs"])
    async def derive(self, context: Context) -> Dict[str, Any]:
        """
        Derive normalized features from application data.

        Features include:
        - Equipment age/mileage bands
        - Business type (startup vs established)
        - Geography/industry flags
        - Risk indicators

        Returns:
            dict with features
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        validate_output = context.step_output("validate")
        verify_output = context.step_output("verify")

        if validate_output.get("status") == "failed":
            return {"features": {}}

        app_data = validate_output.get("application_data", {})
        check_results = verify_output.get("check_results", {})

        logger.info(f"[derive] Processing application {workflow_input.application_id}")

        features = {}

        try:
            # Extract scores from check results
            for check_type, result in check_results.items():
                if isinstance(result, dict):
                    if result.get("check_type") == CheckType.CREDIT_CHECK.value and result.get("score"):
                        features["guarantor.fico"] = result["score"]
                    elif result.get("check_type") == CheckType.KYB.value and result.get("score"):
                        features["business.paynet_score"] = result["score"]
                    elif result.get("check_type") == CheckType.BANK_VERIFICATION.value and result.get("score"):
                        features["bank.balance"] = result["score"]

            # Calculate derived fields
            equipment = app_data.get("equipment", [])
            current_year = datetime.now().year

            for idx, equip in enumerate(equipment):
                year = equip.get("year")
                if year:
                    features[f"equipment.{idx}.age_years"] = max(0, current_year - year)
                mileage = equip.get("mileage")
                if mileage:
                    features[f"equipment.{idx}.mileage"] = mileage
                    if mileage < 50000:
                        features[f"equipment.{idx}.mileage_band"] = "low"
                    elif mileage < 100000:
                        features[f"equipment.{idx}.mileage_band"] = "medium"
                    else:
                        features[f"equipment.{idx}.mileage_band"] = "high"

            # Business age calculation
            years_in_business = 0
            for result in check_results.values():
                if isinstance(result, dict) and result.get("raw_response"):
                    details = result["raw_response"].get("details", {})
                    if "years_in_business" in details:
                        years_in_business = details["years_in_business"]
                        break

            features["business.years_in_business"] = years_in_business
            features["business.is_startup"] = years_in_business < 2

            # Loan details
            loan_request = app_data.get("loan_request", {})
            if loan_request:
                features["loan.amount"] = loan_request.get("amount")
                features["loan.term_months"] = loan_request.get("term_months")
                features["loan.down_payment"] = loan_request.get("down_payment")

            logger.info(f"[derive] Derived {len(features)} features")

        except Exception as e:
            logger.error(f"[derive] Failed: {str(e)}")

        return {"features": features}

    # =========================================================================
    # Step 5: Calculate Overall Risk
    # =========================================================================
    @step(timeout="5s", retries=0, parents=["derive"])
    async def assess(self, context: Context) -> Dict[str, Any]:
        """
        Calculate overall risk assessment from all check results.

        Aggregates individual check risk levels into an overall
        application risk score.

        Returns:
            dict with overall_risk and risk_flags
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        validate_output = context.step_output("validate")
        verify_output = context.step_output("verify")
        analyze_output = context.step_output("analyze_docs")

        if validate_output.get("status") == "failed":
            return {
                "overall_risk": None,
                "risk_flags": [],
            }

        logger.info(f"[assess] Application {workflow_input.application_id}")

        # Combine risk flags from all steps
        risk_flags = list(verify_output.get("risk_flags", []))
        risk_flags.extend(analyze_output.get("risk_flags", []))

        check_results = verify_output.get("check_results", {})

        risk_counts = {
            RiskLevel.LOW.value: 0,
            RiskLevel.MEDIUM.value: 0,
            RiskLevel.HIGH.value: 0,
            RiskLevel.CRITICAL.value: 0,
        }

        for result in check_results.values():
            if isinstance(result, dict) and result.get("risk_level"):
                risk_level = result["risk_level"]
                if risk_level in risk_counts:
                    risk_counts[risk_level] += 1

        # Determine overall risk
        if risk_counts[RiskLevel.CRITICAL.value] > 0:
            overall_risk = RiskLevel.CRITICAL.value
        elif risk_counts[RiskLevel.HIGH.value] >= 2:
            overall_risk = RiskLevel.CRITICAL.value
        elif risk_counts[RiskLevel.HIGH.value] > 0:
            overall_risk = RiskLevel.HIGH.value
        elif risk_counts[RiskLevel.MEDIUM.value] >= 2:
            overall_risk = RiskLevel.HIGH.value
        elif risk_counts[RiskLevel.MEDIUM.value] > 0:
            overall_risk = RiskLevel.MEDIUM.value
        else:
            overall_risk = RiskLevel.LOW.value

        logger.info(f"[assess] Overall risk: {overall_risk}")

        return {
            "overall_risk": overall_risk,
            "risk_flags": risk_flags,
        }

    # =========================================================================
    # Step 6: Request Documents Based on Failed Checks
    # =========================================================================
    @step(timeout="10s", retries=1, parents=["assess"])
    async def request_docs(self, context: Context) -> Dict[str, Any]:
        """
        Automatically request documents based on failed checks and risk flags.

        This step analyzes the check results and risk assessment to determine
        what additional documents are needed to proceed with the application.

        Returns:
            dict with documents_requested count
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        validate_output = context.step_output("validate")
        verify_output = context.step_output("verify")
        assess_output = context.step_output("assess")

        if validate_output.get("status") == "failed":
            return {"documents_requested": 0}

        check_results = verify_output.get("check_results", {})
        overall_risk = assess_output.get("overall_risk")

        # Check if any documents need to be requested
        has_failures = any(
            r.get("status") in [CheckStatus.FAILED.value, CheckStatus.NEEDS_REVIEW.value]
            for r in check_results.values()
            if isinstance(r, dict)
        )

        has_high_risk = overall_risk in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]

        if not has_failures and not has_high_risk:
            logger.info(f"[request_docs] No documents needed for {workflow_input.application_id}")
            return {"documents_requested": 0}

        logger.info(f"[request_docs] Processing {workflow_input.application_id}")

        documents_requested = 0
        db = get_db_session()
        try:
            application = load_application(db, workflow_input.application_id)
            if application:
                # Reconstruct CheckResult objects for the service
                reconstructed_results = {
                    key: reconstruct_check_result(result)
                    for key, result in check_results.items()
                    if isinstance(result, dict)
                }

                created_requests = document_request_service.process_check_results(
                    db=db,
                    application=application,
                    check_results=reconstructed_results,
                    overall_risk=RiskLevel(overall_risk) if overall_risk else None,
                )

                if created_requests:
                    documents_requested = len(created_requests)
                    logger.info(f"[request_docs] Created {documents_requested} requests")
        except Exception as e:
            logger.error(f"[request_docs] Failed: {str(e)}")
        finally:
            db.close()

        return {"documents_requested": documents_requested}

    # =========================================================================
    # Step 7: Run Lender Matching (REVIEW step only)
    # =========================================================================
    @step(timeout="30s", retries=2, parents=["assess"])
    async def match(self, context: Context) -> Dict[str, Any]:
        """
        Match application against all lender programs.

        This step only runs during the REVIEW step. It:
        - Evaluates each lender program's criteria
        - Calculates fit scores
        - Ranks matches by eligibility and score
        - Assigns terms and rates for eligible matches

        Returns:
            dict with match_results, best_lender_program_id, best_term_months, best_interest_rate
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        validate_output = context.step_output("validate")

        empty_result = {
            "match_results": [],
            "best_lender_program_id": None,
            "best_term_months": None,
            "best_interest_rate": None,
        }

        if workflow_input.step != ApplicationStep.REVIEW:
            return empty_result

        if validate_output.get("status") == "failed":
            return empty_result

        if not workflow_input.run_matching:
            return empty_result

        logger.info(f"[match] Running for {workflow_input.application_id}")

        results = []
        best_lender_program_id = None
        best_term_months = None
        best_interest_rate = None

        db = get_db_session()
        try:
            application = load_application(db, workflow_input.application_id)
            if not application:
                return empty_result

            programs = db.query(LenderProgram).all()

            for program in programs:
                try:
                    eligible, fit_score, reasons, per_rule = evaluate_application_against_program(
                        application, program
                    )

                    lender_name = program.lender.name if program.lender else None

                    assigned_term = None
                    assigned_interest_rate = None
                    if eligible:
                        assigned_term = calculate_assigned_term(program, application)
                        assigned_interest_rate = calculate_interest_rate(program, application, fit_score)

                    results.append({
                        "lender_program_id": str(program.id),
                        "lender_name": lender_name,
                        "program_name": program.name,
                        "eligible": eligible,
                        "fit_score": fit_score,
                        "reasons": reasons,
                        "criterion_results": per_rule,
                        "assigned_term_months": assigned_term,
                        "assigned_interest_rate": assigned_interest_rate,
                    })

                except Exception as e:
                    logger.error(f"[match] Program {program.id} failed: {str(e)}")
                    results.append({
                        "lender_program_id": str(program.id),
                        "lender_name": program.lender.name if program.lender else None,
                        "program_name": program.name,
                        "eligible": False,
                        "fit_score": 0,
                        "reasons": f"Evaluation error: {str(e)}",
                        "criterion_results": [],
                    })

            # Sort results: eligible first, then by fit_score descending
            results.sort(key=lambda r: (not r["eligible"], -(r.get("fit_score") or 0)))

            # Determine best terms among all eligible programs
            eligible_results = [r for r in results if r.get("eligible")]
            if eligible_results:
                sorted_eligible = sorted(
                    eligible_results,
                    key=lambda r: (
                        r.get("fit_score") or 0,
                        r.get("assigned_term_months") or 0,
                        -(r.get("assigned_interest_rate") or 100),
                    ),
                    reverse=True
                )

                best_program = sorted_eligible[0]
                best_lender_program_id = best_program.get("lender_program_id")
                best_term_months = best_program.get("assigned_term_months")
                best_interest_rate = best_program.get("assigned_interest_rate")

                logger.info(
                    f"[match] Best: {best_program.get('lender_name')} - {best_program.get('program_name')} "
                    f"({best_term_months}mo @ {best_interest_rate}%)"
                )

            eligible_count = sum(1 for r in results if r["eligible"])
            logger.info(f"[match] Complete: {eligible_count}/{len(results)} eligible")

        finally:
            db.close()

        return {
            "match_results": results,
            "best_lender_program_id": best_lender_program_id,
            "best_term_months": best_term_months,
            "best_interest_rate": best_interest_rate,
        }

    # =========================================================================
    # Step 8: Persist Results
    # =========================================================================
    @step(timeout="10s", retries=3, parents=["match", "request_docs"])
    async def persist(self, context: Context) -> Dict[str, Any]:
        """
        Persist workflow results to the database.

        Creates a MatchRun record with all check results and
        MatchResult records for each lender program evaluation.

        Returns:
            dict with match_run_id and status
        """
        input_data = context.workflow_input()
        workflow_input = WorkflowInput(input_data)
        validate_output = context.step_output("validate")
        verify_output = context.step_output("verify")
        analyze_output = context.step_output("analyze_docs")
        derive_output = context.step_output("derive")
        assess_output = context.step_output("assess")
        request_docs_output = context.step_output("request_docs")
        match_output = context.step_output("match")

        logger.info(f"[persist] Saving {workflow_input.application_id}")

        completed_at = datetime.utcnow()
        started_at = datetime.utcnow()

        # Determine final workflow status
        validation_errors = validate_output.get("errors", [])
        check_results = verify_output.get("check_results", {})

        if validation_errors:
            workflow_status = WorkflowStatus.FAILED.value
        elif any(r.get("status") == CheckStatus.FAILED.value for r in check_results.values() if isinstance(r, dict)):
            workflow_status = WorkflowStatus.PARTIAL.value
        else:
            workflow_status = WorkflowStatus.COMPLETED.value

        db = get_db_session()
        try:
            application = load_application(db, workflow_input.application_id)
            if not application:
                return {"match_run_id": None, "status": "failed"}

            # Create MatchRun
            match_run = MatchRun(
                application_id=workflow_input.application_id,
                status=workflow_status,
                check_results={
                    "step": workflow_input.step.value,
                    "checks": check_results,
                    "document_results": analyze_output.get("document_results", {}),
                    "derived_features": derive_output.get("features", {}),
                    "risk_assessment": {
                        "overall_risk": assess_output.get("overall_risk"),
                        "risk_flags": assess_output.get("risk_flags", []),
                    },
                    "validation_errors": validation_errors,
                    "warnings": verify_output.get("warnings", []) + analyze_output.get("warnings", []),
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                },
            )

            # Create MatchResults for lender matching (REVIEW step)
            match_results = match_output.get("match_results", [])
            if workflow_input.step == ApplicationStep.REVIEW and match_results:
                for result in match_results:
                    match_result = MatchResult(
                        lender_program_id=UUID(result["lender_program_id"]),
                        eligible=result["eligible"],
                        fit_score=result.get("fit_score"),
                        reasons=result.get("reasons"),
                        criterion_results={
                            "lender_name": result.get("lender_name"),
                            "program_name": result.get("program_name"),
                            "criteria": result.get("criterion_results", []),
                            "assigned_term_months": result.get("assigned_term_months"),
                            "assigned_interest_rate": result.get("assigned_interest_rate"),
                        },
                    )
                    match_run.results.append(match_result)

                # Update Application with assigned lender program
                best_lender_program_id = match_output.get("best_lender_program_id")
                if best_lender_program_id:
                    application.assigned_lender_program_id = UUID(best_lender_program_id)
                    application.assigned_term_months = match_output.get("best_term_months")
                    application.assigned_interest_rate = match_output.get("best_interest_rate")

                    if application.loan_request:
                        if match_output.get("best_term_months"):
                            application.loan_request.term_months = match_output["best_term_months"]
                    else:
                        from app.models.application import LoanRequest as LoanRequestModel
                        application.loan_request = LoanRequestModel(
                            application_id=workflow_input.application_id,
                            term_months=match_output.get("best_term_months"),
                        )

                # Update criteria_met from the best match result
                best_match = next(
                    (r for r in match_results if r.get("lender_program_id") == best_lender_program_id),
                    None
                )
                if best_match:
                    criteria_list = best_match.get("criterion_results", [])
                    application.criteria_total = len(criteria_list)
                    application.criteria_met = sum(1 for c in criteria_list if c.get("passed", False))

            db.add(match_run)

            # Update application workflow state
            application.workflow_step = workflow_input.step.value
            application.workflow_status = workflow_status
            application.risk_level = assess_output.get("overall_risk")
            application.risk_flags = assess_output.get("risk_flags", [])

            # Determine review status and application status (only at REVIEW step)
            if workflow_input.step == ApplicationStep.REVIEW:
                all_checks_passed = all(
                    r.get("status") == CheckStatus.COMPLETED.value
                    for r in check_results.values()
                    if isinstance(r, dict)
                )
                has_eligible_match = any(r.get("eligible", False) for r in match_results)
                documents_requested = request_docs_output.get("documents_requested", 0) > 0

                if documents_requested:
                    application.review_status = ReviewStatus.PENDING_MANUAL_REVIEW
                    application.requires_manual_review = True
                    application.status = ApplicationStatus.PENDING_DOCS
                elif all_checks_passed and has_eligible_match:
                    application.review_status = ReviewStatus.AUTO_APPROVED
                    application.requires_manual_review = False
                    application.status = ApplicationStatus.APPROVED
                else:
                    application.review_status = ReviewStatus.PENDING_MANUAL_REVIEW
                    application.requires_manual_review = True
                    application.status = ApplicationStatus.PROCESSING

            db.commit()
            db.refresh(match_run)

            # Log audit action
            log_action(
                db,
                actor="system",
                entity_type="workflow",
                entity_id=match_run.id,
                action=f"workflow_step_{workflow_input.step.value}",
                application_id=workflow_input.application_id,
                payload={
                    "step": workflow_input.step.value,
                    "status": workflow_status,
                    "risk_flags_count": len(assess_output.get("risk_flags", [])),
                    "match_results_count": len(match_results),
                },
            )

            logger.info(f"[persist] Saved match_run_id={match_run.id}")

            return {
                "match_run_id": str(match_run.id),
                "status": workflow_status,
            }

        finally:
            db.close()


# =============================================================================
# Convenience Functions for Running Workflows
# =============================================================================

async def run_application_workflow(
    application: Application,
    step: ApplicationStep,
    db: Session,
    programs: Optional[List[LenderProgram]] = None,
) -> MatchRun:
    """
    Main entry point for running the application workflow via Hatchet.

    Args:
        application: The application to process
        step: The current step in the application form
        db: Database session (not used directly, workflow creates its own)
        programs: Lender programs for matching (not used, workflow queries)

    Returns:
        MatchRun with workflow results
    """
    from app.workflows.hatchet_client import hatchet
    
    if hatchet is None:
        # Fallback to sync execution if Hatchet is not configured
        logger.warning("Hatchet not configured, running workflow synchronously")
        return run_workflow_sync(application, step, db, programs)
    
    logger.info(f"Starting Hatchet workflow for application {application.id} at step {step}")

    workflow_input = {
        "application_id": str(application.id),
        "step": step.value,
        "run_matching": step == ApplicationStep.REVIEW,
    }

    # Run the workflow via Hatchet
    workflow_ref = hatchet.admin.run_workflow(
        "application-workflow",
        workflow_input,
    )
    
    # Wait for completion
    await workflow_ref.result()
    
    # Get the match run from database
    match_run = db.query(MatchRun).filter(
        MatchRun.application_id == application.id
    ).order_by(MatchRun.created_at.desc()).first()

    logger.info(f"Hatchet workflow completed for application {application.id}")
    return match_run


def run_workflow_sync(
    application: Application,
    step: ApplicationStep,
    db: Session,
    programs: Optional[List[LenderProgram]] = None,
) -> MatchRun:
    """
    Synchronous wrapper for run_application_workflow.

    Use this when calling from sync code (e.g., FastAPI endpoints without async).
    """
    return asyncio.run(
        run_application_workflow(application, step, db, programs)
    )
