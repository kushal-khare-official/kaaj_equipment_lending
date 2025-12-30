"""
Workflow API Router for step-based application processing.

This router provides endpoints to trigger workflow execution at each
step of the application form. It enables:
- Real-time verification as users progress through the form
- Early detection of issues (KYC/KYB failures, credit problems)
- Incremental risk assessment
- Final lender matching on review
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models.application import Application, MatchRun
from app.models.lender import LenderProgram
from app.services.audit_logger import log_action
from app.shared.workflow_enums import (
    ApplicationStep,
    CheckType,
    CheckStatus,
    WorkflowStatus,
    RiskLevel,
    STEP_CHECKS,
)
from app.workflows.application_workflow import run_application_workflow
from app.shared.enums import ReviewStatus
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])


# =============================================================================
# Request/Response Schemas
# =============================================================================

class WorkflowTriggerRequest(BaseModel):
    """Request to trigger workflow at a specific step."""
    step: str  # ApplicationStep value
    run_in_background: bool = False


class CheckResultOut(BaseModel):
    """Output schema for a single check result."""
    check_type: str
    status: str
    vendor: Optional[str] = None
    verified: Optional[bool] = None
    score: Optional[int] = None
    risk_level: Optional[str] = None
    flags: List[str] = []
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class WorkflowResultOut(BaseModel):
    """Output schema for workflow execution result."""
    match_run_id: UUID
    step: str
    status: str
    checks: Dict[str, CheckResultOut] = {}
    derived_features: Dict[str, Any] = {}
    risk_assessment: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = []
    warnings: List[str] = []
    match_results_count: int = 0


class StepChecksOut(BaseModel):
    """Output schema for checks configured at a step."""
    step: str
    checks: List[str]
    description: str


class ManualReviewRequest(BaseModel):
    """Request for manual review action."""
    action: str  # "approve" or "reject"
    reviewer: str = "underwriter"


class ReviewStatusOut(BaseModel):
    """Output schema for application review status."""
    application_id: str
    review_status: str
    requires_manual_review: bool
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/{application_id}/trigger", response_model=WorkflowResultOut)
async def trigger_workflow(
    application_id: str,
    payload: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger workflow execution for an application at a specific step.

    This endpoint runs the appropriate verification checks for the given
    step and returns results. Use this as users progress through the form.

    Steps and their checks:
    - business_search: No checks (just search)
    - business_details: KYB, Business Credit, Online Presence, UCC Search
    - guarantor_info: KYC, Personal Credit Check
    - equipment_info: Feature derivation only
    - loan_details: Bank Verification
    - documents: Document Analysis, Bank Statement Analysis
    - review: Full lender matching
    - submitted: Final state

    Args:
        application_id: UUID of the application
        payload: Step to trigger and options

    Returns:
        WorkflowResultOut with check results and risk assessment
    """
    # Validate application ID
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    # Validate step
    try:
        step = ApplicationStep(payload.step)
    except ValueError:
        valid_steps = [s.value for s in ApplicationStep]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step. Must be one of: {valid_steps}"
        )

    # Load application with relationships
    application = (
        db.query(Application)
        .options(
            joinedload(Application.guarantors),
            joinedload(Application.business_credit),
            joinedload(Application.equipment),
            joinedload(Application.loan_request),
            joinedload(Application.document_requests),
        )
        .filter(Application.id == app_uuid)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Load lender programs for REVIEW step
    programs = None
    if step == ApplicationStep.REVIEW:
        programs = (
            db.query(LenderProgram)
            .options(joinedload(LenderProgram.lender), joinedload(LenderProgram.criteria))
            .all()
        )

    # Run workflow
    if payload.run_in_background:
        # Run in background task
        background_tasks.add_task(
            _run_workflow_task,
            application.id,
            step,
            programs,
        )
        # Return immediately with pending status
        return WorkflowResultOut(
            match_run_id=UUID("00000000-0000-0000-0000-000000000000"),
            step=step.value,
            status=WorkflowStatus.PENDING.value,
            validation_errors=[],
            warnings=["Workflow running in background"],
        )
    else:
        # Run synchronously
        match_run = await run_application_workflow(application, step, db, programs)
        return _format_workflow_result(match_run)


@router.get("/{application_id}/latest", response_model=WorkflowResultOut)
def get_latest_workflow_result(
    application_id: str,
    db: Session = Depends(get_db),
):
    """
    Get the latest workflow result for an application.

    Returns the most recent MatchRun with all check results
    and risk assessment.
    """
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    match_run = (
        db.query(MatchRun)
        .filter(MatchRun.application_id == app_uuid)
        .order_by(MatchRun.created_at.desc())
        .first()
    )

    if not match_run:
        raise HTTPException(status_code=404, detail="No workflow results found")

    return _format_workflow_result(match_run)


@router.get("/{application_id}/history")
def get_workflow_history(
    application_id: str,
    db: Session = Depends(get_db),
):
    """
    Get all workflow executions for an application.

    Returns a list of all MatchRuns ordered by creation time,
    showing the progression of checks as the user filled out the form.
    """
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    match_runs = (
        db.query(MatchRun)
        .filter(MatchRun.application_id == app_uuid)
        .order_by(MatchRun.created_at.desc())
        .all()
    )

    results = []
    for run in match_runs:
        check_results = run.check_results or {}
        results.append({
            "match_run_id": run.id,
            "step": check_results.get("step"),
            "status": run.status,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "risk_level": check_results.get("risk_assessment", {}).get("overall_risk"),
            "flags_count": len(check_results.get("risk_assessment", {}).get("risk_flags", [])),
            "match_results_count": len(run.results) if run.results else 0,
        })

    return {"history": results}


@router.get("/{application_id}/run/{match_run_id}", response_model=WorkflowResultOut)
def get_workflow_run(
    application_id: str,
    match_run_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a specific workflow run result by match_run_id.

    This allows viewing check results for any workflow step,
    not just the latest one.
    """
    try:
        app_uuid = UUID(application_id)
        run_uuid = UUID(match_run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id or match_run_id")

    match_run = (
        db.query(MatchRun)
        .filter(MatchRun.id == run_uuid, MatchRun.application_id == app_uuid)
        .first()
    )

    if not match_run:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    return _format_workflow_result(match_run)


@router.get("/steps")
def list_workflow_steps():
    """
    List all workflow steps and their configured checks.

    Returns information about what checks run at each step of the
    application form. Use this to understand what validations
    will occur as users progress.
    """
    steps = []
    descriptions = {
        ApplicationStep.BUSINESS_SEARCH: "Initial business search - no verification checks",
        ApplicationStep.BUSINESS_DETAILS: "Business verification including KYB, credit, and online presence",
        ApplicationStep.GUARANTOR_INFO: "Personal verification including KYC and credit check",
        ApplicationStep.EQUIPMENT_INFO: "Equipment data validation and feature derivation",
        ApplicationStep.LOAN_DETAILS: "Loan terms and bank verification",
        ApplicationStep.DOCUMENTS: "AI-powered document analysis and verification",
        ApplicationStep.REVIEW: "Final review and lender matching",
        ApplicationStep.SUBMITTED: "Application submitted - final state",
    }

    for step in ApplicationStep:
        checks = STEP_CHECKS.get(step, [])
        steps.append(StepChecksOut(
            step=step.value,
            checks=[c.value for c in checks],
            description=descriptions.get(step, ""),
        ))

    return {"steps": steps}


@router.post("/{application_id}/retry/{check_type}")
async def retry_failed_check(
    application_id: str,
    check_type: str,
    db: Session = Depends(get_db),
):
    """
    Retry a specific failed check.

    Use this when a check failed due to a transient error and you
    want to retry just that check without re-running the entire workflow.

    Args:
        application_id: UUID of the application
        check_type: The check type to retry (e.g., "kyc", "kyb", "credit_check")

    Returns:
        Updated check result
    """
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    try:
        check_type_enum = CheckType(check_type)
    except ValueError:
        valid_types = [c.value for c in CheckType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid check type. Must be one of: {valid_types}"
        )

    # Load application
    application = (
        db.query(Application)
        .options(
            joinedload(Application.guarantors),
            joinedload(Application.business_credit),
        )
        .filter(Application.id == app_uuid)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Import verification service
    from app.services.verification_checks import verification_service

    # Build check data
    app_data = {
        "business_name": application.business_name,
    }

    if application.guarantors:
        primary = next((g for g in application.guarantors if g.is_primary), application.guarantors[0])
        app_data["first_name"] = primary.first_name
        app_data["last_name"] = primary.last_name

    # Run the specific check
    results = await verification_service.run_checks_parallel(
        checks=[check_type_enum],
        application_data=app_data,
    )

    result = results.get(check_type)

    # Log the retry
    log_action(
        db,
        actor="system",
        entity_type="check_retry",
        entity_id=None,
        action=f"retry_{check_type}",
        application_id=application.id,
        payload={
            "check_type": check_type,
            "status": result.status.value if result else "failed",
        },
    )

    if result:
        return {
            "check_type": result.check_type.value,
            "status": result.status.value,
            "verified": result.verified,
            "score": result.score,
            "risk_level": result.risk_level.value if result.risk_level else None,
            "flags": result.flags,
            "error": result.error,
        }
    else:
        raise HTTPException(status_code=500, detail="Check execution failed")


@router.get("/{application_id}/review-status", response_model=ReviewStatusOut)
def get_review_status(
    application_id: str,
    db: Session = Depends(get_db),
):
    """
    Get the current review status of an application.

    Returns the review status, whether manual review is required,
    and review details if reviewed.
    """
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    application = db.query(Application).filter(Application.id == app_uuid).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return ReviewStatusOut(
        application_id=str(application.id),
        review_status=application.review_status.value if application.review_status else "pending",
        requires_manual_review=application.requires_manual_review or False,
        reviewed_by=application.reviewed_by,
        reviewed_at=application.reviewed_at.isoformat() if application.reviewed_at else None,
    )


class ManualMatchRequest(BaseModel):
    """Request for manually matching application to lender program."""
    lender_program_id: str
    term_months: Optional[int] = None
    interest_rate: Optional[float] = None


@router.post("/{application_id}/review", response_model=ReviewStatusOut)
def manual_review(
    application_id: str,
    payload: ManualReviewRequest,
    db: Session = Depends(get_db),
):
    """
    Perform manual review action on an application.

    Args:
        application_id: UUID of the application
        payload: Action ("approve" or "reject") and reviewer name

    Returns:
        Updated review status
    """
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    application = db.query(Application).filter(Application.id == app_uuid).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    # Update review status and application status based on action
    from app.shared.enums import ApplicationStatus
    
    if payload.action == "approve":
        application.review_status = ReviewStatus.MANUALLY_APPROVED
        application.status = ApplicationStatus.APPROVED
    else:
        application.review_status = ReviewStatus.MANUALLY_REJECTED
        application.status = ApplicationStatus.DECLINED

    application.reviewed_by = payload.reviewer
    application.reviewed_at = datetime.utcnow()
    application.requires_manual_review = False  # Review complete

    db.commit()
    db.refresh(application)

    # Log audit action
    log_action(
        db,
        actor=payload.reviewer,
        entity_type="application",
        entity_id=application.id,
        action=f"manual_review_{payload.action}",
        application_id=application.id,
        payload={
            "action": payload.action,
            "previous_status": application.review_status.value,
        },
    )

    logger.info(f"Application {application_id} manually {payload.action}d by {payload.reviewer}")

    return ReviewStatusOut(
        application_id=str(application.id),
        review_status=application.review_status.value,
        requires_manual_review=application.requires_manual_review or False,
        reviewed_by=application.reviewed_by,
        reviewed_at=application.reviewed_at.isoformat() if application.reviewed_at else None,
    )


@router.post("/{application_id}/rerun", response_model=WorkflowResultOut)
async def rerun_workflow(
    application_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Rerun the complete workflow for an application.

    This endpoint re-executes all verification checks and lender matching
    from scratch. Use this when data has changed or when retrying after
    transient failures.

    Args:
        application_id: UUID of the application

    Returns:
        WorkflowResultOut with updated check results
    """
    try:
        app_uuid = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    # Load application with relationships
    application = (
        db.query(Application)
        .options(
            joinedload(Application.guarantors),
            joinedload(Application.business_credit),
            joinedload(Application.equipment),
            joinedload(Application.loan_request),
            joinedload(Application.document_requests),
        )
        .filter(Application.id == app_uuid)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Reset review status to pending for re-evaluation
    application.review_status = ReviewStatus.PENDING
    application.requires_manual_review = False
    application.reviewed_by = None
    application.reviewed_at = None
    db.commit()

    # Load lender programs for matching
    programs = (
        db.query(LenderProgram)
        .options(joinedload(LenderProgram.lender), joinedload(LenderProgram.criteria))
        .all()
    )

    # Run complete workflow at REVIEW step (runs all checks)
    match_run = await run_application_workflow(application, ApplicationStep.REVIEW, db, programs)

    # Log the rerun action
    log_action(
        db,
        actor="underwriter",
        entity_type="workflow",
        entity_id=match_run.id,
        action="rerun_workflow",
        application_id=application.id,
        payload={
            "status": match_run.status,
            "match_results_count": len(match_run.results) if match_run.results else 0,
        },
    )

    logger.info(f"Workflow rerun completed for application {application_id}")

    return _format_workflow_result(match_run)


@router.post("/{application_id}/manual-match")
def manual_match(
    application_id: str,
    payload: ManualMatchRequest,
    db: Session = Depends(get_db),
):
    """
    Manually match an application to a lender program.

    This allows underwriters to bypass automated matching and directly
    assign a lender program to an application, with custom terms if desired.

    Args:
        application_id: UUID of the application
        payload: Lender program ID and optional custom terms

    Returns:
        Updated application with loan terms
    """
    from app.models.application import MatchRun, MatchResult, LoanRequest as LoanRequestModel

    try:
        app_uuid = UUID(application_id)
        program_uuid = UUID(payload.lender_program_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id or lender_program_id")

    application = (
        db.query(Application)
        .options(joinedload(Application.loan_request))
        .filter(Application.id == app_uuid)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    program = (
        db.query(LenderProgram)
        .options(joinedload(LenderProgram.lender))
        .filter(LenderProgram.id == program_uuid)
        .first()
    )
    if not program:
        raise HTTPException(status_code=404, detail="Lender program not found")

    # Get term and rate from payload or program defaults
    term_months = payload.term_months or program.term_default or program.term_max or 60
    interest_rate = payload.interest_rate or (float(program.interest_rate_default) if program.interest_rate_default else 8.0)

    # Update or create loan request with matched terms
    if application.loan_request:
        application.loan_request.term_months = term_months
    else:
        loan_request = LoanRequestModel(
            application_id=application.id,
            term_months=term_months,
        )
        db.add(loan_request)

    # Create a manual match run and result
    match_run = MatchRun(
        application_id=application.id,
        status="completed",
        check_results={
            "step": "review",
            "manual_match": True,
            "matched_by": "underwriter",
        },
    )
    db.add(match_run)
    db.flush()

    match_result = MatchResult(
        match_run_id=match_run.id,
        lender_program_id=program.id,
        eligible=True,
        fit_score=100,  # Manual match gets full score
        reasons="Manually matched by underwriter",
    )
    db.add(match_result)

    # Update application status and assigned lender program
    from app.shared.enums import ApplicationStatus
    
    application.review_status = ReviewStatus.MANUALLY_APPROVED
    application.status = ApplicationStatus.APPROVED  # Set application status to approved
    application.reviewed_by = "underwriter"
    application.reviewed_at = datetime.utcnow()
    application.assigned_lender_program_id = program.id
    application.assigned_term_months = term_months
    application.assigned_interest_rate = interest_rate

    db.commit()

    # Log the manual match
    log_action(
        db,
        actor="underwriter",
        entity_type="match",
        entity_id=match_run.id,
        action="manual_match",
        application_id=application.id,
        payload={
            "lender_program_id": str(program.id),
            "lender_name": program.lender.name if program.lender else None,
            "program_name": program.name,
            "term_months": term_months,
            "interest_rate": interest_rate,
        },
    )

    logger.info(f"Application {application_id} manually matched to program {program.name}")

    return {
        "success": True,
        "application_id": str(application.id),
        "lender_program_id": str(program.id),
        "lender_name": program.lender.name if program.lender else None,
        "program_name": program.name,
        "term_months": term_months,
        "interest_rate": interest_rate,
    }


# =============================================================================
# Helper Functions
# =============================================================================

def _format_workflow_result(match_run: MatchRun) -> WorkflowResultOut:
    """Format a MatchRun into the response schema."""
    check_results = match_run.check_results or {}

    checks = {}
    for key, check_data in check_results.get("checks", {}).items():
        if isinstance(check_data, dict):
            checks[key] = CheckResultOut(
                check_type=check_data.get("check_type", key),
                status=check_data.get("status", "unknown"),
                vendor=check_data.get("vendor"),
                verified=check_data.get("verified"),
                score=check_data.get("score"),
                risk_level=check_data.get("risk_level"),
                flags=check_data.get("flags", []),
                error=check_data.get("error"),
                duration_ms=check_data.get("duration_ms"),
            )

    return WorkflowResultOut(
        match_run_id=match_run.id,
        step=check_results.get("step", "unknown"),
        status=match_run.status,
        checks=checks,
        derived_features=check_results.get("derived_features", {}),
        risk_assessment=check_results.get("risk_assessment"),
        validation_errors=check_results.get("validation_errors", []),
        warnings=check_results.get("warnings", []),
        match_results_count=len(match_run.results) if match_run.results else 0,
    )


async def _run_workflow_task(
    application_id: UUID,
    step: ApplicationStep,
    programs: Optional[List[LenderProgram]],
):
    """Background task to run workflow."""
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        application = (
            db.query(Application)
            .options(
                joinedload(Application.guarantors),
                joinedload(Application.business_credit),
                joinedload(Application.equipment),
                joinedload(Application.loan_request),
                joinedload(Application.document_requests),
            )
            .filter(Application.id == application_id)
            .first()
        )

        if application:
            await run_application_workflow(application, step, db, programs)

    except Exception as e:
        logger.error(f"Background workflow failed: {str(e)}")
    finally:
        db.close()
