from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from datetime import datetime

from app.models.lender import Lender, LenderProgram, LenderCriteria, PolicyVersion
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
def get_lender(lender_id: str, db: Session = Depends(get_db)):
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    return lender


@router.patch("/{lender_id}", response_model=LenderOut)
def update_lender(lender_id: str, payload: LenderUpdate, db: Session = Depends(get_db)):
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    if payload.name:
        lender.name = payload.name
    if payload.programs:
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

