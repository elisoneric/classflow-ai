"""
APScheduler process entrypoint. Runs as its own container/process — never
inside the API process — so scaling the API to multiple replicas can't
double-schedule a job. See PROJECT.md §9.

Registers two persistent jobs:
- generate_daily_sessions: cron, 00:05 local time — creates today's
  ClassSession rows from active TimetableSlots and schedules each one's
  first reminder.
- enqueue_poll_inbound_email: interval — pushes an IMAP poll onto the RQ
  queue every IMAP_POLL_INTERVAL_SECONDS.

Per-session reminder/deadline jobs are added dynamically at runtime (by
generate_daily_sessions and by ClassSessionService via APSchedulerGateway),
not registered here.
"""

import asyncio
import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.jobs.tasks import enqueue_poll_inbound_email, generate_daily_sessions

from sqlalchemy.engine import make_url

logger = logging.getLogger(__name__)


def _sync_database_url(async_url: str) -> str:
    url = make_url(async_url)
    return str(url._replace(drivername="postgresql+psycopg2"))


def build_scheduler() -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_jobstore(
        SQLAlchemyJobStore(url=_sync_database_url(settings.database_url)), alias="default"
    )

    scheduler.add_job(
        generate_daily_sessions,
        CronTrigger(hour=0, minute=5, timezone=settings.timezone),
        id="generate-daily-sessions",
        replace_existing=True,
    )
    scheduler.add_job(
        enqueue_poll_inbound_email,
        IntervalTrigger(seconds=settings.imap_poll_interval_seconds),
        id="poll-inbound-email",
        replace_existing=True,
    )
    return scheduler


async def main() -> None:
    configure_logging()

    scheduler = None
    retries = 15
    for attempt in range(1, retries + 1):
        try:
            scheduler = build_scheduler()
            scheduler.start()
            break
        except Exception as exc:
            if attempt == retries:
                logger.error("Could not connect to database after %d attempts: %s", retries, exc)
                raise
            logger.warning("Database not ready yet (attempt %d/%d): %s. Retrying in 2s...", attempt, retries, exc)
            await asyncio.sleep(2)

    logger.info("Scheduler started (timezone=%s)", get_settings().timezone)
    try:
        await asyncio.Event().wait()
    finally:
        if scheduler:
            scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
