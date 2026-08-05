import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ReminderStatus
from app.infrastructure.db.models import Reminder


class SqlAlchemyReminderRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_session(self, class_session_id: uuid.UUID) -> list[Reminder]:
        result = await self._session.execute(
            select(Reminder)
            .where(Reminder.class_session_id == class_session_id)
            .order_by(Reminder.attempt_number)
        )
        return list(result.scalars().all())

    async def list_pending_for_session(self, class_session_id: uuid.UUID) -> list[Reminder]:
        result = await self._session.execute(
            select(Reminder).where(
                Reminder.class_session_id == class_session_id,
                Reminder.status == ReminderStatus.SENT,
            )
        )
        return list(result.scalars().all())

    async def add(self, reminder: Reminder) -> None:
        self._session.add(reminder)
