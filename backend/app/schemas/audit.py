from uuid import UUID
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: UUID
    actor: str | None
    entity_type: str
    entity_id: UUID | None
    action: str
    payload: dict | None

    class Config:
        from_attributes = True

