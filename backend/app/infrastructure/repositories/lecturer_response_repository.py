from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import LecturerResponse


class SqlAlchemyLecturerResponseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, response: LecturerResponse) -> None:
        self._session.add(response)
