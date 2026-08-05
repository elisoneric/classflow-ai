"""
RQ task functions plus the lightweight `enqueue_*` functions APScheduler calls
directly (PROJECT.md §9, ADR-5: APScheduler decides *when*, RQ decides *how*).

`enqueue_*` functions are referenced from apscheduler_gateway.py by their
importable string path (e.g. "app.infrastructure.jobs.tasks:enqueue_send_reminder")
so APScheduler can pickle/store them in its jobstore — they must stay
module-level, synchronous, and side-effect-free beyond pushing to the queue.

The `*_task` functions are what the RQ worker actually executes. They're sync
wrappers (RQ's native execution model) around async application-layer calls.
"""

import asyncio
import logging
import uuid
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.domain.enums import CourseStatus, DayOfWeek
from app.infrastructure.ai.gemini_interpreter import GeminiInterpreter
from app.infrastructure.db.models import ClassSession, Course, TimetableSlot
from app.infrastructure.db.session import async_session_maker
from app.infrastructure.email.imap_poller import ImapEmailPoller
from app.infrastructure.email.reply_cleaner import clean_reply
from app.infrastructure.factories import build_class_session_service
from app.infrastructure.jobs.queue import get_queue
from app.infrastructure.scheduler.apscheduler_gateway import get_apscheduler_gateway

logger = logging.getLogger(__name__)

_WEEKDAYS = [
    DayOfWeek.MONDAY,
    DayOfWeek.TUESDAY,
    DayOfWeek.WEDNESDAY,
    DayOfWeek.THURSDAY,
    DayOfWeek.FRIDAY,
    DayOfWeek.SATURDAY,
    DayOfWeek.SUNDAY,
]


# --- enqueue_* : called directly by APScheduler, must stay lightweight ---


def enqueue_send_reminder(class_session_id: str, attempt_number: int) -> None:
    get_queue().enqueue(send_reminder_task, class_session_id, attempt_number)


def enqueue_check_deadline(class_session_id: str, attempt_number: int) -> None:
    get_queue().enqueue(check_deadline_task, class_session_id, attempt_number)


def enqueue_poll_inbound_email() -> None:
    get_queue().enqueue(poll_inbound_email_task)


# --- *_task : executed by the RQ worker (worker.py) ---


def send_reminder_task(class_session_id: str, attempt_number: int) -> None:
    asyncio.run(_send_reminder_async(class_session_id, attempt_number))


async def _send_reminder_async(class_session_id: str, attempt_number: int) -> None:
    async with async_session_maker() as db:
        service = build_class_session_service(db)
        try:
            await service.send_scheduled_reminder(uuid.UUID(class_session_id), attempt_number)
        except Exception:
            logger.exception(
                "send_reminder_task failed for session=%s attempt=%s",
                class_session_id,
                attempt_number,
            )


def check_deadline_task(class_session_id: str, attempt_number: int) -> None:
    asyncio.run(_check_deadline_async(class_session_id, attempt_number))


async def _check_deadline_async(class_session_id: str, attempt_number: int) -> None:
    async with async_session_maker() as db:
        service = build_class_session_service(db)
        try:
            await service.handle_deadline(uuid.UUID(class_session_id), attempt_number)
        except Exception:
            logger.exception(
                "check_deadline_task failed for session=%s attempt=%s",
                class_session_id,
                attempt_number,
            )


def poll_inbound_email_task() -> None:
    asyncio.run(_poll_inbound_email_async())


async def _poll_inbound_email_async() -> None:
    poller = ImapEmailPoller()
    try:
        messages = await poller.fetch_unseen()
    except Exception:
        logger.exception("poll_inbound_email_task: IMAP fetch failed")
        return

    for message in messages:
        try:
            await _process_inbound_message(message)
        except Exception:
            logger.exception("poll_inbound_email_task: failed processing uid=%s", message.uid)
        finally:
            # Always mark seen — an unmatched or malformed message would
            # otherwise be reprocessed on every poll forever.
            try:
                await poller.mark_seen(message.uid)
            except Exception:
                logger.exception("poll_inbound_email_task: mark_seen failed uid=%s", message.uid)


async def _process_inbound_message(message) -> None:
    if not message.in_reply_to:
        logger.info("Skipping inbound email with no In-Reply-To/References: uid=%s", message.uid)
        return

    async with async_session_maker() as db:
        service = build_class_session_service(db)
        prepared = await service.prepare_response_context(message.in_reply_to)
        if prepared is None:
            logger.info("No matching pending reminder for inbound email uid=%s", message.uid)
            return
        reminder, _class_session, context = prepared

        cleaned = clean_reply(message.body)
        interpreter = GeminiInterpreter()
        interpretation = await interpreter.interpret(cleaned, context)

        await service.handle_lecturer_response(
            reminder.id,
            raw_message=message.body,
            cleaned_message=cleaned,
            received_at=message.received_at,
            interpretation=interpretation,
        )


# --- generate_daily_sessions : called directly by APScheduler (no RQ hop —
# pure DB work + scheduling other jobs, no external I/O). See PROJECT.md §9 job #1.


async def generate_daily_sessions() -> None:
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    today: date = datetime.now(tz).date()
    weekday = _WEEKDAYS[datetime.now(tz).weekday()]
    gateway = get_apscheduler_gateway()

    async with async_session_maker() as db:
        result = await db.execute(
            select(TimetableSlot)
            .join(Course, TimetableSlot.course_id == Course.id)
            .where(
                TimetableSlot.is_active.is_(True),
                TimetableSlot.day_of_week == weekday,
                Course.status == CourseStatus.ACTIVE,
            )
        )
        slots = list(result.scalars().all())

        for slot in slots:
            session_obj = ClassSession(
                course_id=slot.course_id,
                timetable_slot_id=slot.id,
                session_date=today,
                scheduled_start_time=slot.start_time,
                scheduled_end_time=slot.end_time,
                venue=slot.venue,
                mode=slot.mode,
            )
            db.add(session_obj)
            try:
                await db.flush()
            except IntegrityError:
                # Already generated for today (unique constraint) — idempotent skip,
                # matters if the scheduler restarts and re-runs this job.
                await db.rollback()
                continue

            reminder_at = datetime.combine(today, slot.reminder_time, tzinfo=tz).astimezone(UTC)
            await gateway.schedule_reminder(session_obj.id, 1, reminder_at)
            await db.commit()
            logger.info(
                "Generated session %s for course=%s date=%s, reminder scheduled at %s",
                session_obj.id,
                slot.course_id,
                today,
                reminder_at,
            )
