"""
Hatchet Workflow Implementation for Lender Matching Platform.

This module implements a comprehensive workflow system that:
1. Validates application completeness at each step
2. Runs verification checks (KYC, KYB, Credit, Bank, etc.) in parallel
3. Derives features from application data
4. Matches against lender programs with fit scoring
5. Persists results with full audit trail

The workflow is designed to run incrementally as the user progresses through
the application form, providing real-time feedback and early detection of issues.

Hatchet Features Demonstrated:
- @hatchet.workflow() - Workflow definition
- @hatchet.step() - Individual workflow steps
- Parallel execution via asyncio.gather
- Retry logic with exponential backoff
- Step dependencies and DAG execution
- Context passing between steps
- Error handling and recovery
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.application import Application, MatchRun, MatchResult
from app.models.lender import LenderProgram
from app.services.verification_checks import verification_service, VerificationService
from app.services.document_analysis import document_analysis_service
from app.services.feature_derivation import derive_application_features
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
    WorkflowCheckResults,
    STEP_CHECKS,
    REQUIRED_CHECKS,
    OPTIONAL_CHECKS,
)
from app.shared.enums import ReviewStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Hatchet Workflow Definition
# =============================================================================
#
# NOTE: This is structured to work with the Hatchet SDK when available.
# For now, it provides a compatible interface that can be used directly
# or easily adapted to Hatchet's decorator-based workflow system.
#
# When Hatchet is integrated, simply add the decorators:
#
# @hatchet.workflow(name="application-workflow")
# class ApplicationWorkflow:
#     @hatchet.step(retries=3)
#     async def validate_application(self, ctx):
#         ...
#
# =============================================================================


class WorkflowContext:
    """
    Context object passed between workflow steps.

    Holds the current state of the workflow execution including:
    - Application data
    - Check results from previous steps
    - Derived features
    - Error state
    """

    def __init__(
        self,
        application_id: UUID,
        step: ApplicationStep,
        application_data: Dict[str, Any],
    ):
        self.application_id = application_id
        self.step = step
        self.application_data = application_data
        self.check_results: Dict[str, CheckResult] = {}
        self.derived_features: Dict[str, Any] = {}
        self.match_results: List[Dict[str, Any]] = []
        self.validation_errors: List[str] = []
        self.warnings: List[str] = []
        self.risk_flags: List[str] = []
        self.overall_risk: Optional[RiskLevel] = None
        self.workflow_status: WorkflowStatus = WorkflowStatus.PENDING
        self.started_at: datetime = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.documents_requested: int = 0  # Count of documents requested in this run


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
    """

    def __init__(
        self,
        verification_service: VerificationService = verification_service,
    ):
        self.verification_service = verification_service

    # =========================================================================
    # Step 1: Validate Application Completeness
    # =========================================================================
    async def validate_application(
        self,
        ctx: WorkflowContext,
    ) -> WorkflowContext:
        """
        Validate that required data is present for the current step.

        This is the first step that runs for every workflow execution.
        It checks that the minimum required fields are populated before
        proceeding with verification checks.

        Hatchet config:
            retries: 0 (validation should not retry)
            timeout: 5s
        """
        logger.info(f"Validating application {ctx.application_id} at step {ctx.step}")
        ctx.workflow_status = WorkflowStatus.RUNNING

        errors = []
        warnings = []

        # Common validation
        if not ctx.application_data.get("merchant_email"):
            errors.append("Merchant email is required")

        # Step-specific validation
        if ctx.step in [ApplicationStep.BUSINESS_DETAILS, ApplicationStep.GUARANTOR_INFO,
                        ApplicationStep.EQUIPMENT_INFO, ApplicationStep.LOAN_DETAILS,
                        ApplicationStep.DOCUMENTS, ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
            if not ctx.application_data.get("business_name"):
                errors.append("Business name is required")

        if ctx.step in [ApplicationStep.GUARANTOR_INFO, ApplicationStep.EQUIPMENT_INFO,
                        ApplicationStep.LOAN_DETAILS, ApplicationStep.DOCUMENTS,
                        ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
            guarantors = ctx.application_data.get("guarantors", [])
            if not guarantors:
                errors.append("At least one guarantor is required")
            else:
                primary = next((g for g in guarantors if g.get("is_primary")), None)
                if not primary:
                    errors.append("Primary guarantor must be designated")
                elif not primary.get("first_name") or not primary.get("last_name"):
                    errors.append("Primary guarantor name is required")

        if ctx.step in [ApplicationStep.EQUIPMENT_INFO, ApplicationStep.LOAN_DETAILS,
                        ApplicationStep.DOCUMENTS, ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
            equipment = ctx.application_data.get("equipment", [])
            if not equipment:
                warnings.append("No equipment information provided")

        if ctx.step in [ApplicationStep.LOAN_DETAILS, ApplicationStep.DOCUMENTS,
                        ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
            loan_request = ctx.application_data.get("loan_request", {})
            if not loan_request.get("amount"):
                errors.append("Loan amount is required")

        if ctx.step in [ApplicationStep.REVIEW, ApplicationStep.SUBMITTED]:
            # Final validation - all data required
            if not ctx.application_data.get("business_credit", {}).get("paynet_score"):
                warnings.append("PayNet score not available")

        ctx.validation_errors = errors
        ctx.warnings = warnings

        if errors:
            ctx.workflow_status = WorkflowStatus.FAILED
            logger.warning(f"Application {ctx.application_id} failed validation: {errors}")
        else:
            logger.info(f"Application {ctx.application_id} passed validation")

        return ctx

    # =========================================================================
    # Step 2: Run Verification Checks in Parallel
    # =========================================================================
    async def run_verification_checks(
        self,
        ctx: WorkflowContext,
    ) -> WorkflowContext:
        """
        Run verification checks appropriate for the current step.

        Checks are executed in parallel using asyncio.gather for performance.
        Results are aggregated and any failures are tracked.

        Hatchet config:
            retries: 3
            backoff: exponential
            timeout: 60s
            parents: [validate_application]
        """
        if ctx.workflow_status == WorkflowStatus.FAILED:
            logger.info(f"Skipping verification checks - validation failed")
            return ctx

        checks_to_run = STEP_CHECKS.get(ctx.step, [])
        if not checks_to_run:
            logger.info(f"No verification checks configured for step {ctx.step}")
            return ctx

        logger.info(f"Running {len(checks_to_run)} verification checks for step {ctx.step}")

        # Build application data dict for checks
        app_data = self._build_check_data(ctx)

        # Run checks in parallel
        try:
            results = await self.verification_service.run_checks_parallel(
                checks=checks_to_run,
                application_data=app_data,
            )
            ctx.check_results.update(results)

            # Aggregate risk flags
            for check_type, result in results.items():
                if isinstance(result, CheckResult):
                    ctx.risk_flags.extend(result.flags)

                    # Track failures
                    if result.status == CheckStatus.FAILED:
                        if CheckType(check_type) in REQUIRED_CHECKS:
                            ctx.validation_errors.append(f"{check_type} check failed: {result.error}")
                        else:
                            ctx.warnings.append(f"{check_type} check failed: {result.error}")

                    # Track needs review
                    if result.status == CheckStatus.NEEDS_REVIEW:
                        ctx.warnings.append(f"{check_type} requires manual review")

            logger.info(f"Completed verification checks with {len(ctx.risk_flags)} risk flags")

        except Exception as e:
            logger.error(f"Verification checks failed: {str(e)}")
            ctx.validation_errors.append(f"Verification checks failed: {str(e)}")

        return ctx

    # =========================================================================
    # Step 3: Document Analysis (for DOCUMENTS step)
    # =========================================================================
    async def analyze_documents(
        self,
        ctx: WorkflowContext,
    ) -> WorkflowContext:
        """
        Analyze uploaded documents using AI.

        This step only runs during the DOCUMENTS step when documents
        have been uploaded. It performs:
        - Document type verification
        - Data extraction
        - Fraud detection
        - Bank statement analysis

        Hatchet config:
            retries: 2
            timeout: 120s
            parents: [run_verification_checks]
        """
        if ctx.step != ApplicationStep.DOCUMENTS:
            return ctx

        if ctx.workflow_status == WorkflowStatus.FAILED:
            logger.info(f"Skipping document analysis - validation failed")
            return ctx

        documents = ctx.application_data.get("documents", [])
        if not documents:
            logger.info("No documents to analyze")
            return ctx

        logger.info(f"Analyzing {len(documents)} documents")

        try:
            # Prepare validation data
            validation_data = {
                "business_name": ctx.application_data.get("business_name"),
                "account_holder": ctx.application_data.get("guarantors", [{}])[0].get("first_name"),
            }

            # Analyze documents in parallel
            results = await document_analysis_service.analyze_documents_parallel(
                documents=documents,
                validation_data=validation_data,
            )

            # Store results
            for url, result in results.items():
                ctx.check_results[f"document_{url}"] = result
                ctx.risk_flags.extend(result.flags)

                if result.status == CheckStatus.NEEDS_REVIEW:
                    ctx.warnings.append(f"Document requires review: {url}")

            logger.info(f"Document analysis complete")

        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            ctx.warnings.append(f"Document analysis failed: {str(e)}")

        return ctx

    # =========================================================================
    # Step 4: Derive Application Features
    # =========================================================================
    async def derive_features(
        self,
        ctx: WorkflowContext,
    ) -> WorkflowContext:
        """
        Derive normalized features from application data.

        Features include:
        - Equipment age/mileage bands
        - Business type (startup vs established)
        - Geography/industry flags
        - Risk indicators

        Hatchet config:
            retries: 1
            timeout: 10s
            parents: [run_verification_checks, analyze_documents]
        """
        if ctx.workflow_status == WorkflowStatus.FAILED:
            return ctx

        logger.info(f"Deriving features for application {ctx.application_id}")

        try:
            # Get features from check results
            features = {}

            # Extract scores from check results
            for check_type, result in ctx.check_results.items():
                if isinstance(result, CheckResult):
                    if result.check_type == CheckType.CREDIT_CHECK and result.score:
                        features["guarantor.fico"] = result.score
                    elif result.check_type == CheckType.KYB and result.score:
                        features["business.paynet_score"] = result.score
                    elif result.check_type == CheckType.BANK_VERIFICATION and result.score:
                        features["bank.balance"] = result.score

            # Calculate derived fields
            equipment = ctx.application_data.get("equipment", [])
            current_year = datetime.now().year

            for idx, equip in enumerate(equipment):
                year = equip.get("year")
                if year:
                    features[f"equipment.{idx}.age_years"] = max(0, current_year - year)
                mileage = equip.get("mileage")
                if mileage:
                    features[f"equipment.{idx}.mileage"] = mileage
                    # Mileage bands
                    if mileage < 50000:
                        features[f"equipment.{idx}.mileage_band"] = "low"
                    elif mileage < 100000:
                        features[f"equipment.{idx}.mileage_band"] = "medium"
                    else:
                        features[f"equipment.{idx}.mileage_band"] = "high"

            # Business age calculation
            business_credit = ctx.application_data.get("business_credit", {})
            years_in_business = 0
            for result in ctx.check_results.values():
                if isinstance(result, CheckResult) and result.raw_response:
                    details = result.raw_response.get("details", {})
                    if "years_in_business" in details:
                        years_in_business = details["years_in_business"]
                        break

            features["business.years_in_business"] = years_in_business
            features["business.is_startup"] = years_in_business < 2

            # Loan details
            loan_request = ctx.application_data.get("loan_request", {})
            if loan_request:
                features["loan.amount"] = loan_request.get("amount")
                features["loan.term_months"] = loan_request.get("term_months")
                features["loan.down_payment"] = loan_request.get("down_payment")

            ctx.derived_features = features
            logger.info(f"Derived {len(features)} features")

        except Exception as e:
            logger.error(f"Feature derivation failed: {str(e)}")
            ctx.warnings.append(f"Feature derivation incomplete: {str(e)}")

        return ctx

    # =========================================================================
    # Step 5: Calculate Overall Risk
    # =========================================================================
    async def assess_risk(
        self,
        ctx: WorkflowContext,
    ) -> WorkflowContext:
        """
        Calculate overall risk assessment from all check results.

        Aggregates individual check risk levels into an overall
        application risk score.

        Hatchet config:
            retries: 0
            timeout: 5s
            parents: [derive_features]
        """
        if ctx.workflow_status == WorkflowStatus.FAILED:
            return ctx

        logger.info(f"Assessing risk for application {ctx.application_id}")

        risk_counts = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: 0,
            RiskLevel.CRITICAL: 0,
        }

        for result in ctx.check_results.values():
            if isinstance(result, CheckResult) and result.risk_level:
                risk_counts[result.risk_level] += 1

        # Determine overall risk
        if risk_counts[RiskLevel.CRITICAL] > 0:
            ctx.overall_risk = RiskLevel.CRITICAL
        elif risk_counts[RiskLevel.HIGH] >= 2:
            ctx.overall_risk = RiskLevel.CRITICAL
        elif risk_counts[RiskLevel.HIGH] > 0:
            ctx.overall_risk = RiskLevel.HIGH
        elif risk_counts[RiskLevel.MEDIUM] >= 2:
            ctx.overall_risk = RiskLevel.HIGH
        elif risk_counts[RiskLevel.MEDIUM] > 0:
            ctx.overall_risk = RiskLevel.MEDIUM
        else:
            ctx.overall_risk = RiskLevel.LOW

        logger.info(f"Overall risk assessment: {ctx.overall_risk}")
        return ctx

    # =========================================================================
    # Step 6: Request Documents Based on Failed Checks
    # =========================================================================
    async def request_documents(
        self,
        ctx: WorkflowContext,
        db: Session,
        application: Application,
    ) -> WorkflowContext:
        """
        Automatically request documents based on failed checks and risk flags.

        This step analyzes the check results and risk assessment to determine
        what additional documents are needed to proceed with the application.

        Hatchet config:
            retries: 1
            timeout: 10s
            parents: [assess_risk]
        """
        if ctx.workflow_status == WorkflowStatus.FAILED:
            return ctx

        # Check if any documents need to be requested
        has_failures = any(
            r.status in [CheckStatus.FAILED, CheckStatus.NEEDS_REVIEW]
            for r in ctx.check_results.values()
            if isinstance(r, CheckResult)
        )

        has_high_risk = ctx.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        if not has_failures and not has_high_risk:
            logger.info(f"No document requests needed for application {ctx.application_id}")
            return ctx

        logger.info(f"Processing document requests for application {ctx.application_id}")

        try:
            # Get required documents based on check results
            created_requests = document_request_service.process_check_results(
                db=db,
                application=application,
                check_results=ctx.check_results,
                overall_risk=ctx.overall_risk,
            )

            if created_requests:
                ctx.documents_requested = len(created_requests)
                ctx.warnings.append(
                    f"Additional documents requested: {len(created_requests)} document(s)"
                )
                logger.info(
                    f"Created {len(created_requests)} document requests for application {ctx.application_id}"
                )

        except Exception as e:
            logger.error(f"Document request processing failed: {str(e)}")
            ctx.warnings.append(f"Document request processing failed: {str(e)}")

        return ctx

    # =========================================================================
    # Step 7: Run Lender Matching (REVIEW step only)
    # =========================================================================
    async def run_lender_matching(
        self,
        ctx: WorkflowContext,
        application: Application,
        programs: List[LenderProgram],
    ) -> WorkflowContext:
        """
        Match application against all lender programs.

        This step only runs during the REVIEW step. It:
        - Evaluates each lender program's criteria
        - Calculates fit scores
        - Ranks matches by eligibility and score
        - Assigns terms and rates for eligible matches

        Hatchet config:
            retries: 2
            timeout: 30s
            parents: [assess_risk]
        """
        if ctx.step != ApplicationStep.REVIEW:
            return ctx

        if ctx.workflow_status == WorkflowStatus.FAILED:
            return ctx

        logger.info(f"Running lender matching for application {ctx.application_id}")

        results = []

        # Evaluate each program (can be parallelized for large program sets)
        for program in programs:
            try:
                eligible, fit_score, reasons, per_rule = evaluate_application_against_program(
                    application, program
                )

                lender_name = program.lender.name if program.lender else None

                # Calculate assigned terms if eligible
                assigned_term = None
                assigned_interest_rate = None
                if eligible:
                    assigned_term = calculate_assigned_term(program, application)
                    assigned_interest_rate = calculate_interest_rate(program, application, fit_score)

                results.append({
                    "lender_program_id": program.id,
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
                logger.error(f"Failed to evaluate program {program.id}: {str(e)}")
                results.append({
                    "lender_program_id": program.id,
                    "lender_name": program.lender.name if program.lender else None,
                    "program_name": program.name,
                    "eligible": False,
                    "fit_score": 0,
                    "reasons": f"Evaluation error: {str(e)}",
                    "criterion_results": [],
                })

        # Sort results: eligible first, then by fit_score descending
        results.sort(key=lambda r: (not r["eligible"], -(r.get("fit_score") or 0)))
        ctx.match_results = results
        
        # Determine best terms among all eligible programs
        # Best = highest tenure + lowest interest rate
        eligible_results = [r for r in results if r.get("eligible")]
        if eligible_results:
            best_term = max(
                (r.get("assigned_term_months") for r in eligible_results if r.get("assigned_term_months")),
                default=None
            )
            best_rate = min(
                (r.get("assigned_interest_rate") for r in eligible_results if r.get("assigned_interest_rate")),
                default=None
            )
            
            logger.info(
                f"Best available terms: {best_term} months at {best_rate}% "
                f"(from {len(eligible_results)} eligible programs)"
            )

        eligible_count = sum(1 for r in results if r["eligible"])
        logger.info(f"Matching complete: {eligible_count}/{len(results)} programs eligible")

        return ctx

    # =========================================================================
    # Step 7: Persist Results
    # =========================================================================
    async def persist_results(
        self,
        ctx: WorkflowContext,
        db: Session,
    ) -> MatchRun:
        """
        Persist workflow results to the database.

        Creates a MatchRun record with all check results and
        MatchResult records for each lender program evaluation.

        Hatchet config:
            retries: 3
            timeout: 10s
            parents: [run_lender_matching]
        """
        logger.info(f"Persisting results for application {ctx.application_id}")

        ctx.completed_at = datetime.utcnow()

        # Determine final workflow status
        if ctx.validation_errors:
            ctx.workflow_status = WorkflowStatus.FAILED
        elif any(r.status == CheckStatus.FAILED for r in ctx.check_results.values()
                 if isinstance(r, CheckResult)):
            ctx.workflow_status = WorkflowStatus.PARTIAL
        else:
            ctx.workflow_status = WorkflowStatus.COMPLETED

        # Serialize check results
        serialized_checks = {}
        for key, result in ctx.check_results.items():
            if isinstance(result, CheckResult):
                serialized_checks[key] = {
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

        # Create MatchRun
        match_run = MatchRun(
            application_id=ctx.application_id,
            status=ctx.workflow_status.value,
            check_results={
                "step": ctx.step.value,
                "checks": serialized_checks,
                "derived_features": ctx.derived_features,
                "risk_assessment": {
                    "overall_risk": ctx.overall_risk.value if ctx.overall_risk else None,
                    "risk_flags": ctx.risk_flags,
                },
                "validation_errors": ctx.validation_errors,
                "warnings": ctx.warnings,
                "started_at": ctx.started_at.isoformat(),
                "completed_at": ctx.completed_at.isoformat() if ctx.completed_at else None,
            },
        )

        # Create MatchResults for lender matching (REVIEW step)
        if ctx.step == ApplicationStep.REVIEW and ctx.match_results:
            for result in ctx.match_results:
                match_result = MatchResult(
                    lender_program_id=result["lender_program_id"],
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

        db.add(match_run)
        db.commit()
        db.refresh(match_run)

        # Log audit action
        log_action(
            db,
            actor="system",
            entity_type="workflow",
            entity_id=match_run.id,
            action=f"workflow_step_{ctx.step.value}",
            application_id=ctx.application_id,
            payload={
                "step": ctx.step.value,
                "status": ctx.workflow_status.value,
                "risk_flags_count": len(ctx.risk_flags),
                "match_results_count": len(ctx.match_results),
            },
        )

        logger.info(f"Workflow results persisted: match_run_id={match_run.id}")
        return match_run

    # =========================================================================
    # Helper Methods
    # =========================================================================
    def _build_check_data(self, ctx: WorkflowContext) -> Dict[str, Any]:
        """Build the data dict needed for verification checks."""
        data = {
            "business_name": ctx.application_data.get("business_name"),
            "tin": ctx.application_data.get("tin"),
        }

        # Get primary guarantor info
        guarantors = ctx.application_data.get("guarantors", [])
        primary = next((g for g in guarantors if g.get("is_primary")), guarantors[0] if guarantors else {})

        data["first_name"] = primary.get("first_name")
        data["last_name"] = primary.get("last_name")
        data["ssn"] = primary.get("ssn")
        data["address"] = primary.get("address")

        # Bank info
        data["account_number"] = ctx.application_data.get("account_number")
        data["routing_number"] = ctx.application_data.get("routing_number")

        # Business info
        data["website"] = ctx.application_data.get("website")
        data["state"] = ctx.application_data.get("state")

        return data


# =============================================================================
# Main Workflow Execution Function
# =============================================================================

async def run_application_workflow(
    application: Application,
    step: ApplicationStep,
    db: Session,
    programs: Optional[List[LenderProgram]] = None,
) -> MatchRun:
    """
    Main entry point for running the application workflow.

    This function orchestrates the workflow execution:
    1. Creates workflow context
    2. Runs validation
    3. Runs verification checks in parallel
    4. Analyzes documents (if applicable)
    5. Derives features
    6. Assesses risk
    7. Runs lender matching (if REVIEW step)
    8. Persists results

    Args:
        application: The application to process
        step: The current step in the application form
        db: Database session
        programs: Lender programs for matching (required for REVIEW step)

    Returns:
        MatchRun with workflow results
    """
    logger.info(f"Starting workflow for application {application.id} at step {step}")

    # Build application data dict
    app_data = {
        "merchant_email": application.merchant_email,
        "business_name": application.business_name,
        "loan_type": application.loan_type,
        "guarantors": [
            {
                "is_primary": g.is_primary,
                "first_name": g.first_name,
                "last_name": g.last_name,
                "fico": g.fico,
                "ssn": getattr(g, "ssn", None),
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

    # Create workflow instance and context
    workflow = ApplicationWorkflow()
    ctx = WorkflowContext(
        application_id=application.id,
        step=step,
        application_data=app_data,
    )

    # Execute workflow steps
    ctx = await workflow.validate_application(ctx)
    ctx = await workflow.run_verification_checks(ctx)
    ctx = await workflow.analyze_documents(ctx)
    ctx = await workflow.derive_features(ctx)
    ctx = await workflow.assess_risk(ctx)
    ctx = await workflow.request_documents(ctx, db, application)

    if step == ApplicationStep.REVIEW and programs:
        ctx = await workflow.run_lender_matching(ctx, application, programs)

    # Update application workflow state
    application.workflow_step = step.value
    application.workflow_status = ctx.workflow_status.value
    application.risk_level = ctx.overall_risk.value if ctx.overall_risk else None
    application.risk_flags = ctx.risk_flags

    # Determine review status based on workflow results (only at REVIEW step)
    if step == ApplicationStep.REVIEW:
        # Check if all checks passed (no failures or needs_review)
        all_checks_passed = all(
            r.status == CheckStatus.COMPLETED
            for r in ctx.check_results.values()
            if isinstance(r, CheckResult)
        )

        # Check if we have any eligible lender matches
        has_eligible_match = any(r.get("eligible", False) for r in ctx.match_results)

        # Check if documents were requested (document fallback triggered)
        documents_requested = ctx.documents_requested > 0

        if documents_requested:
            # Document fallback was triggered - requires manual review
            application.review_status = ReviewStatus.PENDING_MANUAL_REVIEW
            application.requires_manual_review = True
            logger.info(f"Application {application.id} requires manual review (document fallback triggered)")
        elif all_checks_passed and has_eligible_match:
            # All checks passed and we have a lender match - auto approve
            application.review_status = ReviewStatus.AUTO_APPROVED
            application.requires_manual_review = False
            logger.info(f"Application {application.id} auto-approved (all checks passed, lender matched)")
        elif has_eligible_match:
            # Has match but some checks failed/need review - requires manual review
            application.review_status = ReviewStatus.PENDING_MANUAL_REVIEW
            application.requires_manual_review = True
            logger.info(f"Application {application.id} requires manual review (some checks need attention)")
        else:
            # No eligible lender match - stay pending for manual decision
            application.review_status = ReviewStatus.PENDING_MANUAL_REVIEW
            application.requires_manual_review = True
            logger.info(f"Application {application.id} requires manual review (no eligible lender match)")

    db.commit()

    match_run = await workflow.persist_results(ctx, db)

    logger.info(f"Workflow completed for application {application.id}: status={ctx.workflow_status}")
    return match_run


# =============================================================================
# Sync Wrapper for Non-Async Contexts
# =============================================================================

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
