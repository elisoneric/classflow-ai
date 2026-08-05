import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import CourseLecturer


class SqlAlchemyCourseLecturerRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_lecturer(self, lecturer_id: uuid.UUID) -> list[CourseLecturer]:
        result = await self._session.execute(
            select(CourseLecturer).where(CourseLecturer.lecturer_id == lecturer_id)
        )
        return list(result.scalars().all())

    async def list_for_course(self, course_id: uuid.UUID) -> list[CourseLecturer]:
        result = await self._session.execute(
            select(CourseLecturer).where(CourseLecturer.course_id == course_id)
        )
        return list(result.scalars().all())

    async def get(
        self, course_id: uuid.UUID, lecturer_id: uuid.UUID
    ) -> CourseLecturer | None:
        result = await self._session.execute(
            select(CourseLecturer).where(
                CourseLecturer.course_id == course_id, CourseLecturer.lecturer_id == lecturer_id
            )
        )
        return result.scalar_one_or_none()

    async def add(self, link: CourseLecturer) -> None:
        self._session.add(link)

    async def delete(self, link: CourseLecturer) -> None:
        await self._session.delete(link)
