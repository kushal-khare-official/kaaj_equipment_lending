from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import get_db
from app.models.application import Application, MatchRun
from app.models.lender import LenderProgram
from app.schemas.match import MatchRunOut
from app.workflows.match_flow import run_match_workflow
from app.api.routers.mock_vendors import credit_check, kyc_check, kyb_check, business_prefill
from app.services.audit_logger import log_action

router = APIRouter(prefix="/match", tags=["matching"])


@router.post("/{application_id}", response_model=MatchRunOut)
def run_match(application_id: str, db: Session = Depends(get_db)):
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    programs = db.query(LenderProgram).all()
    check_results = {
        "credit": credit_check(),
        "kyc": kyc_check(),
        "kyb": kyb_check(),
        "business_prefill": business_prefill(),
    }
    run = run_match_workflow(app, programs, check_results=check_results)
    db.add(run)
    db.commit()
    db.refresh(run)
    log_action(db, actor="system", entity_type="match_run", entity_id=run.id, action="run_match", application_id=app.id, payload={"check_results": check_results})
    return run


@router.get("/latest/{application_id}", response_model=MatchRunOut)
def latest_match(application_id: str, db: Session = Depends(get_db)):
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    run = (
        db.query(MatchRun)
        .filter(MatchRun.application_id == app_id)
        .order_by(MatchRun.created_at.desc())
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="No match run found")
    return run


@router.get("/application/{application_id}", response_model=list[MatchRunOut])
def list_matches(application_id: str, db: Session = Depends(get_db)):
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    runs = (
        db.query(MatchRun)
        .filter(MatchRun.application_id == app_id)
        .order_by(MatchRun.created_at.desc())
        .limit(20)
        .all()
    )
    return runs

