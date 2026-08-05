import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Course


class SqlAlchemyCourseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, *, semester_id: uuid.UUID | None = None) -> list[Course]:
        stmt = select(Course).order_by(Course.code)
        if semester_id is not None:
            stmt = stmt.where(Course.semester_id == semester_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        result = await self._session.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def add(self, course: Course) -> None:
        self._session.add(course)
