import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import select
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

    async def list_all(
        self,
        *,
        entity_type: AuditEntityType | None = None,
        entity_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        if date_from is not None:
            stmt = stmt.where(
                AuditLog.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            )
        if date_to is not None:
            stmt = stmt.where(
                AuditLog.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
