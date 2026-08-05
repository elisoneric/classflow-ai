import uuid
from typing import Protocol

from app.infrastructure.db.models import Semester


class SemesterRepository(Protocol):
    async def list_all(self) -> list[Semester]: ...
    async def get_by_id(self, semester_id: uuid.UUID) -> Semester | None: ...
    async def add(self, semester: Semester) -> None: ...
