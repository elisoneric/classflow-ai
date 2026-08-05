import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Semester


class SqlAlchemySemesterRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> list[Semester]:
        result = await self._session.execute(select(Semester).order_by(Semester.start_date.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, semester_id: uuid.UUID) -> Semester | None:
        result = await self._session.execute(select(Semester).where(Semester.id == semester_id))
        return result.scalar_one_or_none()

    async def add(self, semester: Semester) -> None:
        self._session.add(semester)
