import uuid
from typing import Protocol

from app.infrastructure.db.models import Course


class CourseRepository(Protocol):
    async def list_all(self, *, semester_id: uuid.UUID | None = None) -> list[Course]: ...
    async def get_by_id(self, course_id: uuid.UUID) -> Course | None: ...
    async def add(self, course: Course) -> None: ...
