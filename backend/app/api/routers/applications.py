import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from uuid import UUID
from app.models.application import Application, Guarantor, BusinessCredit, Equipment, LoanRequest
from app.models.lender import LenderProgram
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut, ApplicationDetailOut, ApplicationListOut
from app.shared.enums import ApplicationStatus
from app.services.audit_logger import log_action
from app.workflows.match_flow import run_match_workflow
from app.api.routers.mock_vendors import credit_check, kyc_check, kyb_check, business_prefill

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationListOut])
def list_applications(db: Session = Depends(get_db)):
    apps = (
        db.query(Application)
        .options(
            joinedload(Application.loan_request),
            joinedload(Application.match_runs),
        )
        .order_by(Application.created_at.desc())
        .limit(100)
        .all()
    )

    # Enrich with loan amount and criteria met info
    results = []
    for app in apps:
        loan_amount = None
        if app.loan_request:
            loan_amount = float(app.loan_request.amount) if app.loan_request.amount else None

        # Get the latest match run to determine criteria met
        criteria_met = None
        fit_score = None
        if app.match_runs:
            latest_run = max(app.match_runs, key=lambda r: r.created_at)
            if latest_run.results:
                eligible_count = sum(1 for r in latest_run.results if r.eligible)
                total_count = len(latest_run.results)
                criteria_met = f"{eligible_count}/{total_count}"
                # Get best fit score from eligible results
                eligible_results = [r for r in latest_run.results if r.eligible]
                if eligible_results:
                    fit_score = max(r.fit_score or 0 for r in eligible_results)

        results.append(ApplicationListOut(
            id=app.id,
            status=app.status,
            merchant_email=app.merchant_email,
            business_name=app.business_name,
            loan_type=app.loan_type,
            loan_amount=loan_amount,
            created_at=app.created_at.isoformat() if app.created_at else None,
            criteria_met=criteria_met,
            fit_score=fit_score,
        ))

    return results


@router.post("", response_model=ApplicationDetailOut)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    app = Application(
        merchant_email=payload.merchant_email,
        status=ApplicationStatus.PROCESSING,
        business_name=payload.business_name,
        loan_type=payload.loan_type,
    )
    app.guarantors = [Guarantor(**g.model_dump()) for g in payload.guarantors]
    if payload.business_credit:
        app.business_credit = BusinessCredit(**payload.business_credit.model_dump())
    app.equipment = [Equipment(**e.model_dump()) for e in payload.equipment]
    if payload.loan_request:
        app.loan_request = LoanRequest(**payload.loan_request.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    log_action(db, actor=app.merchant_email, entity_type="application", entity_id=app.id, action="create_application", application_id=app.id, payload=payload.model_dump())

    # Trigger automatic matching after application creation
    try:
        programs = (
            db.query(LenderProgram)
            .options(joinedload(LenderProgram.lender), joinedload(LenderProgram.criteria))
            .all()
        )
        if programs:
            check_results = {
                "credit": credit_check(),
                "kyc": kyc_check(),
                "kyb": kyb_check(),
                "business_prefill": business_prefill(),
            }
            match_run = run_match_workflow(app, programs, check_results=check_results)
            db.add(match_run)
            db.commit()
            log_action(db, actor="system", entity_type="match_run", entity_id=match_run.id, action="auto_match", application_id=app.id, payload={"check_results": check_results})
            logger.info(f"Auto-match completed for application {app.id}, match_run_id={match_run.id}")
    except Exception as e:
        logger.error(f"Auto-match failed for application {app.id}: {str(e)}")
        # Don't fail the application creation if matching fails

    return app


@router.get("/{application_id}", response_model=ApplicationDetailOut)
def get_application(application_id: str, db: Session = Depends(get_db)):
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    app = (
        db.query(Application)
        .options(
            joinedload(Application.guarantors),
            joinedload(Application.business_credit),
            joinedload(Application.equipment),
            joinedload(Application.loan_request),
            joinedload(Application.document_requests),
        )
        .filter(Application.id == app_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}", response_model=ApplicationDetailOut)
def update_application(application_id: str, payload: ApplicationUpdate, db: Session = Depends(get_db)):
    """Update an application with partial data - used to save progress after each step."""
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")

    app = (
        db.query(Application)
        .options(
            joinedload(Application.guarantors),
            joinedload(Application.business_credit),
            joinedload(Application.equipment),
            joinedload(Application.loan_request),
            joinedload(Application.document_requests),
        )
        .filter(Application.id == app_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update basic fields
    if payload.merchant_email is not None:
        app.merchant_email = payload.merchant_email
    if payload.business_name is not None:
        app.business_name = payload.business_name
    if payload.loan_type is not None:
        app.loan_type = payload.loan_type
    if payload.current_step is not None:
        app.current_step = payload.current_step

    # Update guarantors - replace all if provided
    if payload.guarantors is not None:
        # Delete existing guarantors
        for g in app.guarantors:
            db.delete(g)
        # Add new guarantors
        app.guarantors = [Guarantor(**g.model_dump()) for g in payload.guarantors]

    # Update business_credit - replace if provided
    if payload.business_credit is not None:
        if app.business_credit:
            db.delete(app.business_credit)
        app.business_credit = BusinessCredit(**payload.business_credit.model_dump())

    # Update equipment - replace all if provided
    if payload.equipment is not None:
        # Delete existing equipment
        for e in app.equipment:
            db.delete(e)
        # Add new equipment
        app.equipment = [Equipment(**e.model_dump()) for e in payload.equipment]

    # Update loan_request - replace if provided
    if payload.loan_request is not None:
        if app.loan_request:
            db.delete(app.loan_request)
        app.loan_request = LoanRequest(**payload.loan_request.model_dump())

    db.commit()
    db.refresh(app)
    log_action(db, actor=app.merchant_email, entity_type="application", entity_id=app.id,
               action="update_application", application_id=app.id, payload=payload.model_dump(exclude_none=True))

    return app

