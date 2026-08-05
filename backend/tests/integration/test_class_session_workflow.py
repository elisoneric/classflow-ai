import uuid
from datetime import date, time

import pytest_asyncio
from sqlalchemy import select, text

from app.domain.enums import ClassMode, SessionStatus
from app.infrastructure.db.models import ClassSession
from app.infrastructure.db.session import async_session_maker
from app.infrastructure.factories import build_class_session_service
from app.infrastructure.jobs.tasks import generate_daily_sessions


@pytest_asyncio.fixture
async def scenario(client, auth_headers):
    """Semester + ACTIVE course + primary lecturer, created through the real API."""
    r = await client.post(
        "/api/v1/semesters", headers=auth_headers,
        json={"name": "Test Semester", "start_date": "2026-01-12", "end_date": "2026-05-15"},
    )
    semester_id = r.json()["id"]
    r = await client.post(
        "/api/v1/courses", headers=auth_headers,
        json={
            "semester_id": semester_id, "code": "CSC803", "title": "Advanced Analysis of Algorithms",
            "announcement_email": "class-csc803@example.com",
        },
    )
    course_id = r.json()["id"]
    r = await client.post(
        "/api/v1/lecturers", headers=auth_headers,
        json={"name": "Dr. Adeyemi", "email": "adeyemi@example.com"},
    )
    lecturer_id = r.json()["id"]
    await client.post(
        f"/api/v1/courses/{course_id}/lecturers", headers=auth_headers,
        json={"lecturer_id": lecturer_id, "is_primary": True},
    )
    return {"semester_id": semester_id, "course_id": course_id, "lecturer_id": lecturer_id}


async def _insert_session(course_id: str, status: SessionStatus) -> str:
    async with async_session_maker() as db:
        session_obj = ClassSession(
            course_id=uuid.UUID(course_id), session_date=date.today(),
            scheduled_start_time=time(16, 0), scheduled_end_time=time(18, 0),
            venue="E125", mode=ClassMode.IN_PERSON, status=status,
        )
        db.add(session_obj)
        await db.commit()
        await db.refresh(session_obj)
        return str(session_obj.id)


async def test_override_cancels_reminders_and_announces_immediately(client, auth_headers, scenario):
    session_id = await _insert_session(scenario["course_id"], SessionStatus.SCHEDULED)

    r = await client.post(
        f"/api/v1/class-sessions/{session_id}/override", headers=auth_headers,
        json={"outcome": "CANCELLED", "note": "Lecturer texted me directly"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ANNOUNCED"
    assert r.json()["outcome"] == "CANCELLED"

    r = await client.get(f"/api/v1/class-sessions/{session_id}", headers=auth_headers)
    assert len(r.json()["announcements"]) == 1


async def test_override_works_from_any_status(client, auth_headers, scenario):
    session_id = await _insert_session(scenario["course_id"], SessionStatus.PENDING_REVIEW)
    r = await client.post(
        f"/api/v1/class-sessions/{session_id}/override", headers=auth_headers,
        json={"outcome": "ONLINE"},
    )
    assert r.status_code == 200
    assert r.json()["outcome"] == "ONLINE"


async def test_approve_requires_pending_review_status(client, auth_headers, scenario):
    session_id = await _insert_session(scenario["course_id"], SessionStatus.SCHEDULED)
    r = await client.post(f"/api/v1/class-sessions/{session_id}/approve", headers=auth_headers)
    assert r.status_code == 409


async def test_approve_with_no_ai_interpretation_conflicts(client, auth_headers, scenario):
    session_id = await _insert_session(scenario["course_id"], SessionStatus.PENDING_REVIEW)
    r = await client.post(f"/api/v1/class-sessions/{session_id}/approve", headers=auth_headers)
    assert r.status_code == 409


async def test_reject_delegates_to_override(client, auth_headers, scenario):
    session_id = await _insert_session(scenario["course_id"], SessionStatus.PENDING_REVIEW)
    r = await client.post(
        f"/api/v1/class-sessions/{session_id}/reject", headers=auth_headers,
        json={"outcome": "DELAYED", "start_time": "17:30:00"},
    )
    assert r.status_code == 200
    assert r.json()["outcome"] == "DELAYED"
    assert r.json()["final_start_time"] == "17:30:00"


async def test_get_unknown_session_404s(client, auth_headers):
    r = await client.get(f"/api/v1/class-sessions/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404


async def test_deadline_retry_then_unresolved(scenario):
    """No public endpoint drives this — it's the scheduler's automated path
    (PROJECT.md §9). Exercises send_scheduled_reminder -> handle_deadline
    directly through the service layer, matching how the RQ tasks call it.
    """
    async with async_session_maker() as db:
        from app.infrastructure.db.models import TimetableSlot
        from app.domain.enums import DayOfWeek

        today_weekday = list(DayOfWeek)[date.today().weekday()]
        slot = TimetableSlot(
            course_id=uuid.UUID(scenario["course_id"]), day_of_week=today_weekday,
            start_time=time(16, 0), end_time=time(18, 0), venue="E125", mode=ClassMode.IN_PERSON,
            reminder_time=time(0, 0), response_deadline_minutes=60,
            retry_attempts=1, retry_interval_minutes=15,
        )
        db.add(slot)
        await db.commit()

    await generate_daily_sessions()

    async with async_session_maker() as db:
        result = await db.execute(
            select(ClassSession).where(ClassSession.course_id == uuid.UUID(scenario["course_id"]))
        )
        session_obj = result.scalar_one()
        session_id = session_obj.id

    async with async_session_maker() as db:
        service = build_class_session_service(db)
        await service.send_scheduled_reminder(session_id, 1)
        await service.handle_deadline(session_id, 1)  # retries remain -> schedules attempt 2

    async with async_session_maker() as db:
        job_row = await db.execute(
            text("SELECT id FROM apscheduler_jobs WHERE id = :jid"),
            {"jid": f"send-reminder-{session_id}-2"},
        )
        assert len(job_row.scalars().all()) == 1

    async with async_session_maker() as db:
        service = build_class_session_service(db)
        await service.send_scheduled_reminder(session_id, 2)
        await service.handle_deadline(session_id, 2)  # retries exhausted -> UNRESOLVED

    async with async_session_maker() as db:
        result = await db.execute(select(ClassSession).where(ClassSession.id == session_id))
        final = result.scalar_one()
        assert final.status == SessionStatus.UNRESOLVED
