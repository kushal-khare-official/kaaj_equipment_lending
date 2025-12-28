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
    criteria: List[LenderCriteriaIn] = []


class LenderCreate(BaseModel):
    name: str
    programs: List[LenderProgramIn] = []


class LenderCriteriaOut(LenderCriteriaIn):
    id: UUID

    class Config:
        from_attributes = True


class LenderProgramOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    criteria: List[LenderCriteriaOut] = []

    class Config:
        from_attributes = True


class LenderOut(BaseModel):
    id: UUID
    name: str
    programs: List[LenderProgramOut] = []

    class Config:
        from_attributes = True

