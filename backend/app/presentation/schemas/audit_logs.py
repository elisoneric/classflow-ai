import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import AuditActor, AuditEntityType


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: AuditEntityType
    entity_id: uuid.UUID
    action: str
    actor: AuditActor
    previous_state: dict | None
    new_state: dict | None
    note: str | None
    created_at: datetime
