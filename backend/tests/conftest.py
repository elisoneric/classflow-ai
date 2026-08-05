import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://classflow:changeme@localhost:5432/classflow"
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use-only-32bytes")
os.environ.setdefault("SMTP_HOST", "smtp.invalid.test")
os.environ.setdefault("COURSE_REP_EMAIL", "test-course-rep@example.com")
os.environ.setdefault("COURSE_REP_PASSWORD", "test-password-123")

import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.infrastructure.db.session import async_session_maker, engine  # noqa: E402

# Tables truncated before each DB-touching test. `users` is intentionally
# excluded so the seeded course-rep account survives across the whole run.
_TABLES_TO_CLEAN = (
    "apscheduler_jobs",
    "audit_logs",
    "announcements",
    "lecturer_responses",
    "reminders",
    "class_sessions",
    "timetable_slots",
    "course_lecturers",
    "lecturers",
    "courses",
    "semesters",
    "calendar_exceptions",
)


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TABLES_TO_CLEAN)} CASCADE"))
    yield


@pytest_asyncio.fixture
async def db_session():
    async with async_session_maker() as session:
        yield session
