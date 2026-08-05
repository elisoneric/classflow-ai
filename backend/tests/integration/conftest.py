import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.infrastructure.db.models import User
from app.infrastructure.db.session import async_session_maker
from app.main import app


@pytest_asyncio.fixture
async def course_rep_user():
    settings = get_settings()
    async with async_session_maker() as db:
        existing = await db.execute(select(User).where(User.email == settings.course_rep_email))
        user = existing.scalar_one_or_none()
        if user is None:
            user = User(
                email=settings.course_rep_email,
                hashed_password=hash_password(settings.course_rep_password),
            )
            db.add(user)
            await db.commit()
    return settings.course_rep_email, settings.course_rep_password


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client, course_rep_user):
    email, password = course_rep_user
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
