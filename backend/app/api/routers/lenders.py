from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from datetime import datetime

from app.models.lender import Lender, LenderProgram, LenderCriteria, PolicyVersion
from app.models.application import MatchResult
from app.schemas.lender import LenderCreate, LenderOut, LenderUpdate
from app.services.audit_logger import log_action

router = APIRouter(prefix="/lenders", tags=["lenders"])


@router.post("", response_model=LenderOut)
def create_lender(payload: LenderCreate, db: Session = Depends(get_db)):
    lender = Lender(name=payload.name)
    for p in payload.programs:
        program = LenderProgram(name=p.name, description=p.description)
        program.criteria = [LenderCriteria(**c.model_dump()) for c in p.criteria]
        lender.programs.append(program)
    db.add(lender)
    db.commit()
    db.refresh(lender)
    log_action(db, actor="underwriter", entity_type="lender", entity_id=lender.id, action="create_lender", payload=payload.model_dump())
    return lender


@router.get("", response_model=list[LenderOut])
def list_lenders(db: Session = Depends(get_db)):
    return db.query(Lender).all()


@router.get("/{lender_id}", response_model=LenderOut)
def get_lender(lender_id: UUID, db: Session = Depends(get_db)):
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    return lender


@router.delete("/{lender_id}", status_code=204)
def delete_lender(lender_id: UUID, db: Session = Depends(get_db)):
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    # Nullify match_results references before deleting programs
    program_ids = [p.id for p in lender.programs]
    if program_ids:
        db.query(MatchResult).filter(MatchResult.lender_program_id.in_(program_ids)).update(
            {MatchResult.lender_program_id: None}, synchronize_session=False
        )
    db.delete(lender)
    db.commit()
    log_action(db, actor="underwriter", entity_type="lender", entity_id=lender_id, action="delete_lender", payload={"lender_id": str(lender_id)})
    return None


@router.patch("/{lender_id}", response_model=LenderOut)
def update_lender(lender_id: UUID, payload: LenderUpdate, db: Session = Depends(get_db)):
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    if payload.name:
        lender.name = payload.name
    if payload.programs is not None and len(payload.programs) > 0:
        # Nullify match_results references before deleting old programs
        program_ids = [p.id for p in lender.programs]
        if program_ids:
            db.query(MatchResult).filter(MatchResult.lender_program_id.in_(program_ids)).update(
                {MatchResult.lender_program_id: None}, synchronize_session=False
            )
        lender.programs.clear()
        for p in payload.programs:
            program = LenderProgram(name=p.name, description=p.description)
            program.criteria = [LenderCriteria(**c.model_dump()) for c in p.criteria]
            lender.programs.append(program)
        version = PolicyVersion(lender_id=lender.id, version=str(datetime.utcnow().isoformat()), effective_at=datetime.utcnow(), notes="Updated via API")
        db.add(version)
    db.add(lender)
    db.commit()
    db.refresh(lender)
    log_action(db, actor="underwriter", entity_type="lender", entity_id=lender.id, action="update_lender", payload=payload.model_dump())
    return lender

