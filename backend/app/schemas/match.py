from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.schemas.application import MatchResultOut


class MatchRunOut(BaseModel):
    id: UUID
    results: List[MatchResultOut]

    class Config:
        from_attributes = True

