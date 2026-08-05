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

    async def get_by_id(self, reminder_id: uuid.UUID) -> Reminder | None:
        result = await self._session.execute(select(Reminder).where(Reminder.id == reminder_id))
        return result.scalar_one_or_none()

    async def get_by_outbound_message_id(self, message_id: str) -> Reminder | None:
        result = await self._session.execute(
            select(Reminder).where(Reminder.outbound_message_id == message_id)
        )
        return result.scalar_one_or_none()

    async def add(self, reminder: Reminder) -> None:
        self._session.add(reminder)
