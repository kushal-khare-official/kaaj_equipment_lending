import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from uuid import UUID
from app.models.application import Application, Guarantor, BusinessCredit, Equipment, LoanRequest
from app.models.lender import LenderProgram
from app.schemas.application import ApplicationCreate, ApplicationOut
from app.shared.enums import ApplicationStatus
from app.services.audit_logger import log_action
from app.workflows.match_flow import run_match_workflow
from app.api.routers.mock_vendors import credit_check, kyc_check, kyb_check, business_prefill

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    apps = db.query(Application).order_by(Application.created_at.desc()).limit(100).all()
    return apps


@router.post("", response_model=ApplicationOut)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    app = Application(
        merchant_email=payload.merchant_email,
        status=ApplicationStatus.PROCESSING,
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


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: str, db: Session = Depends(get_db)):
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

