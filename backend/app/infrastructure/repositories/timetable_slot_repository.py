import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import TimetableSlot


class SqlAlchemyTimetableSlotRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_course(self, course_id: uuid.UUID) -> list[TimetableSlot]:
        result = await self._session.execute(
            select(TimetableSlot)
            .where(TimetableSlot.course_id == course_id)
            .order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
        )
        return list(result.scalars().all())

    async def get_by_id(self, slot_id: uuid.UUID) -> TimetableSlot | None:
        result = await self._session.execute(
            select(TimetableSlot).where(TimetableSlot.id == slot_id)
        )
        return result.scalar_one_or_none()

    async def add(self, slot: TimetableSlot) -> None:
        self._session.add(slot)

    async def delete(self, slot: TimetableSlot) -> None:
        await self._session.delete(slot)
