from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from uuid import UUID
from app.models.application import Application, Guarantor, BusinessCredit, Equipment, LoanRequest
from app.schemas.application import ApplicationCreate, ApplicationOut
from app.shared.enums import ApplicationStatus
from app.services.audit_logger import log_action

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

