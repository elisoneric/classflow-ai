import uuid
from datetime import date
from typing import Protocol

from app.domain.enums import SessionStatus
from app.infrastructure.db.models import Announcement, ClassSession, LecturerResponse, Reminder


class ClassSessionRepository(Protocol):
    async def list_all(
        self,
        *,
        course_id: uuid.UUID | None = None,
        status: SessionStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[ClassSession]: ...

    async def get_by_id(self, session_id: uuid.UUID) -> ClassSession | None: ...
    async def add(self, session: ClassSession) -> None: ...


class ReminderRepository(Protocol):
    async def list_for_session(self, class_session_id: uuid.UUID) -> list[Reminder]: ...
    async def list_pending_for_session(self, class_session_id: uuid.UUID) -> list[Reminder]: ...
    async def get_by_id(self, reminder_id: uuid.UUID) -> Reminder | None: ...
    async def get_by_outbound_message_id(self, message_id: str) -> Reminder | None: ...
    async def add(self, reminder: Reminder) -> None: ...


class AnnouncementRepository(Protocol):
    async def add(self, announcement: Announcement) -> None: ...


class LecturerResponseRepository(Protocol):
    async def add(self, response: LecturerResponse) -> None: ...
