import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from app.db import get_db
from app.models.application import Application, MatchRun
from app.models.lender import LenderProgram
from app.schemas.match import MatchRunOut
from app.workflows.match_flow import run_match_workflow
from app.api.routers.mock_vendors import credit_check, kyc_check, kyb_check, business_prefill
from app.services.audit_logger import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match", tags=["matching"])


@router.post("/{application_id}")
def run_match(application_id: str, db: Session = Depends(get_db)):
    try:
        app_id = UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    # Load application with all relationships needed for feature derivation
    app = (
        db.query(Application)
        .options(
            joinedload(Application.guarantors),
            joinedload(Application.business_credit),
            joinedload(Application.equipment),
            joinedload(Application.loan_request),
        )
        .filter(Application.id == app_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    # Load programs with their lender and criteria relationships
    programs = (
        db.query(LenderProgram)
        .options(joinedload(LenderProgram.lender), joinedload(LenderProgram.criteria))
        .all()
    )
    check_results = {
        "credit": credit_check(),
        "kyc": kyc_check(),
        "kyb": kyb_check(),
        "business_prefill": business_prefill(),
    }
    run = run_match_workflow(app, programs, check_results=check_results)
    db.add(run)
    try:
        db.commit()
        db.refresh(run)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    log_action(db, actor="system", entity_type="match_run", entity_id=run.id, action="run_match", application_id=app.id, payload={"check_results": check_results})

    return {
        "id": str(run.id),
        "status": run.status,
        "check_results": run.check_results,
        "results": [
            {
                "lender_program_id": str(r.lender_program_id) if r.lender_program_id else None,
                "lender_name": r.criterion_results.get("lender_name") if r.criterion_results else None,
                "program_name": r.criterion_results.get("program_name") if r.criterion_results else None,
                "eligible": r.eligible,
                "fit_score": r.fit_score,
                "reasons": r.reasons,
                "criterion_results": r.criterion_results.get("criteria") if r.criterion_results else None,
            }
            for r in run.results
        ]
    }


@router.get("/latest/{application_id}")
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
    return {
        "id": str(run.id),
        "status": run.status,
        "check_results": run.check_results,
        "results": [
            {
                "lender_program_id": str(r.lender_program_id) if r.lender_program_id else None,
                "lender_name": r.criterion_results.get("lender_name") if r.criterion_results else None,
                "program_name": r.criterion_results.get("program_name") if r.criterion_results else None,
                "eligible": r.eligible,
                "fit_score": r.fit_score,
                "reasons": r.reasons,
                "criterion_results": r.criterion_results.get("criteria") if r.criterion_results else None,
            }
            for r in run.results
        ]
    }


@router.get("/application/{application_id}")
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
    return [
        {
            "id": str(run.id),
            "status": run.status,
            "check_results": run.check_results,
            "results": [
                {
                    "lender_program_id": str(r.lender_program_id) if r.lender_program_id else None,
                    "lender_name": r.criterion_results.get("lender_name") if r.criterion_results else None,
                    "program_name": r.criterion_results.get("program_name") if r.criterion_results else None,
                    "eligible": r.eligible,
                    "fit_score": r.fit_score,
                    "reasons": r.reasons,
                    "criterion_results": r.criterion_results.get("criteria") if r.criterion_results else None,
                }
                for r in run.results
            ]
        }
        for run in runs
    ]
