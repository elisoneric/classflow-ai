from dataclasses import dataclass

from app.application.auth.ports import UserRepository
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.domain.exceptions import DomainError


class InvalidCredentialsError(DomainError):
    def __init__(self):
        super().__init__("Invalid email or password")


class InvalidTokenError(DomainError):
    def __init__(self):
        super().__init__("Invalid or expired token")


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self._users = user_repository

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        return TokenPair(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise InvalidTokenError() from exc
        if payload.get("type") != "refresh":
            raise InvalidTokenError()
        return create_access_token(payload["sub"])
