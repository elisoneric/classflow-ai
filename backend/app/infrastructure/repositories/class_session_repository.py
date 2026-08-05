import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import SessionStatus
from app.infrastructure.db.models import ClassSession


class SqlAlchemyClassSessionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(
        self,
        *,
        course_id: uuid.UUID | None = None,
        status: SessionStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[ClassSession]:
        stmt = select(ClassSession).order_by(
            ClassSession.session_date, ClassSession.scheduled_start_time
        )
        if course_id is not None:
            stmt = stmt.where(ClassSession.course_id == course_id)
        if status is not None:
            stmt = stmt.where(ClassSession.status == status)
        if date_from is not None:
            stmt = stmt.where(ClassSession.session_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(ClassSession.session_date <= date_to)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, session_id: uuid.UUID) -> ClassSession | None:
        stmt = (
            select(ClassSession)
            .where(ClassSession.id == session_id)
            .options(
                selectinload(ClassSession.reminders),
                selectinload(ClassSession.responses),
                selectinload(ClassSession.announcements),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, session: ClassSession) -> None:
        self._session.add(session)
