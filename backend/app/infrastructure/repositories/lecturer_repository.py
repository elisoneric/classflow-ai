import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Lecturer


class SqlAlchemyLecturerRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> list[Lecturer]:
        result = await self._session.execute(select(Lecturer).order_by(Lecturer.name))
        return list(result.scalars().all())

    async def get_by_id(self, lecturer_id: uuid.UUID) -> Lecturer | None:
        result = await self._session.execute(select(Lecturer).where(Lecturer.id == lecturer_id))
        return result.scalar_one_or_none()

    async def add(self, lecturer: Lecturer) -> None:
        self._session.add(lecturer)

    async def delete(self, lecturer: Lecturer) -> None:
        await self._session.delete(lecturer)
