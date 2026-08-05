import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AuditActor, AuditEntityType
from app.infrastructure.db.models import AuditLog


class SqlAlchemyAuditLogWriter:
    def __init__(self, session: AsyncSession):
        self._session = session

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
    ) -> None:
        self._session.add(
            AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor=actor,
                previous_state=previous_state,
                new_state=new_state,
                note=note,
            )
        )
