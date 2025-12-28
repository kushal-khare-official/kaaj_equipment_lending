from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.application import AuditLog


def log_action(
    db: Session,
    actor: Optional[str],
    entity_type: str,
    entity_id: Optional[UUID],
    action: str,
    payload: Optional[dict] = None,
    application_id: Optional[UUID] = None,
):
    entry = AuditLog(
        application_id=application_id,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload=payload,
    )
    db.add(entry)
    db.commit()
    return entry

