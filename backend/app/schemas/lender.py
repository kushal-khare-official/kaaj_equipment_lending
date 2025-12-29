from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class LenderCriteriaIn(BaseModel):
    field_key: str
    data_type: str
    operator: str
    value_min: Optional[str] = None
    value_max: Optional[str] = None
    values: Optional[list] = None
    pattern: Optional[str] = None
    description: Optional[str] = None


class LenderProgramIn(BaseModel):
    name: str
    description: Optional[str] = None
    term_min: Optional[int] = None
    term_max: Optional[int] = None
    term_default: Optional[int] = None
    term_used_equipment: Optional[int] = None
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    interest_rate_default: Optional[float] = None
    criteria: List[LenderCriteriaIn] = []


class LenderCreate(BaseModel):
    name: str
    programs: List[LenderProgramIn] = []


class LenderUpdate(BaseModel):
    name: Optional[str] = None
    programs: List[LenderProgramIn] = []


class LenderCriteriaOut(LenderCriteriaIn):
    id: UUID

    class Config:
        from_attributes = True


class LenderProgramOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    term_min: Optional[int] = None
    term_max: Optional[int] = None
    term_default: Optional[int] = None
    term_used_equipment: Optional[int] = None
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    interest_rate_default: Optional[float] = None
    criteria: List[LenderCriteriaOut] = []

    class Config:
        from_attributes = True


class LenderOut(BaseModel):
    id: UUID
    name: str
    programs: List[LenderProgramOut] = []

    class Config:
        from_attributes = True

