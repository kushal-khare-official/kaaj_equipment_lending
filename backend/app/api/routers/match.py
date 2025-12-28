from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.application import Application, MatchRun
from app.models.lender import LenderProgram
from app.schemas.match import MatchRunOut
from app.workflows.match_flow import run_match_workflow

router = APIRouter(prefix="/match", tags=["matching"])


@router.post("/{application_id}", response_model=MatchRunOut)
def run_match(application_id: str, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    programs = db.query(LenderProgram).all()
    run = run_match_workflow(app, programs)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

