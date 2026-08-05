from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Announcement


class SqlAlchemyAnnouncementRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, announcement: Announcement) -> None:
        self._session.add(announcement)
