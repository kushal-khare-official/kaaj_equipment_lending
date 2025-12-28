from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.lender import Lender, LenderProgram, LenderCriteria
from app.schemas.lender import LenderCreate, LenderOut

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

