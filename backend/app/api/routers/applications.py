from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.application import Application, Guarantor, BusinessCredit, Equipment, LoanRequest
from app.schemas.application import ApplicationCreate, ApplicationOut
from app.shared.enums import ApplicationStatus

router = APIRouter(prefix="/applications", tags=["applications"])


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
    return app


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: str, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

