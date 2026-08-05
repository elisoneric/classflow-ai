import uuid
from typing import Protocol

from app.infrastructure.db.models import User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_id(self, user_id: str | uuid.UUID) -> User | None: ...
