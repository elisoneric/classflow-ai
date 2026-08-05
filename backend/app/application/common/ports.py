import uuid
from typing import Protocol

from app.domain.enums import AuditActor, AuditEntityType


class AuditLogWriter(Protocol):
    async def record(
        self,
        *,
        entity_type: AuditEntityType,
        entity_id: uuid.UUID,
        action: str,
        actor: AuditActor,
        previous_state: dict | None = None,
        new_state: dict | None = None,
        note: str | None = None,
    ) -> None: ...
