"""
Seeds the single Course Rep user from COURSE_REP_EMAIL / COURSE_REP_PASSWORD.
There is no public /auth/register endpoint by design — this script is the only
way an account gets created. Safe to re-run; it's a no-op if the user exists.
"""

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.infrastructure.db.models import User
from app.infrastructure.db.session import async_session_maker


async def main() -> None:
    settings = get_settings()
    async with async_session_maker() as session:
        existing = await session.execute(
            select(User).where(User.email == settings.course_rep_email)
        )
        if existing.scalar_one_or_none() is not None:
            print(f"User {settings.course_rep_email} already exists — skipping.")
            return

        user = User(
            email=settings.course_rep_email,
            hashed_password=hash_password(settings.course_rep_password),
        )
        session.add(user)
        await session.commit()
        print(f"Seeded course rep user: {settings.course_rep_email}")


if __name__ == "__main__":
    asyncio.run(main())
