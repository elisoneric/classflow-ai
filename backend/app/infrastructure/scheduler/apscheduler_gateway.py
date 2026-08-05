import uuid
from datetime import datetime
from functools import lru_cache

from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.infrastructure.scheduler.job_ids import check_deadline_job_id, send_reminder_job_id

_ENQUEUE_SEND_REMINDER = "app.infrastructure.jobs.tasks:enqueue_send_reminder"
_ENQUEUE_CHECK_DEADLINE = "app.infrastructure.jobs.tasks:enqueue_check_deadline"


def _sync_database_url(async_url: str) -> str:
    return async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


class APSchedulerGateway:
    """Real SchedulerGateway (domain/ports.py). Runs in the API process too,
    but only paused — it never fires jobs itself, it only edits the shared
    SQLAlchemyJobStore table that the real scheduler process
    (scheduler_main.py) reads from. See PROJECT.md §9.
    """

    def __init__(self):
        settings = get_settings()
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_jobstore(
            SQLAlchemyJobStore(url=_sync_database_url(settings.database_url)), alias="default"
        )
        self._scheduler.start(paused=True)

    async def schedule_reminder(
        self, class_session_id: uuid.UUID, attempt_number: int, run_at: datetime
    ) -> str:
        job_id = send_reminder_job_id(class_session_id, attempt_number)
        self._scheduler.add_job(
            _ENQUEUE_SEND_REMINDER,
            "date",
            run_date=run_at,
            id=job_id,
            args=[str(class_session_id), attempt_number],
            replace_existing=True,
        )
        return job_id

    async def schedule_deadline_check(
        self, class_session_id: uuid.UUID, attempt_number: int, run_at: datetime
    ) -> str:
        job_id = check_deadline_job_id(class_session_id, attempt_number)
        self._scheduler.add_job(
            _ENQUEUE_CHECK_DEADLINE,
            "date",
            run_date=run_at,
            id=job_id,
            args=[str(class_session_id), attempt_number],
            replace_existing=True,
        )
        return job_id

    async def cancel_job(self, job_id: str) -> None:
        try:
            self._scheduler.remove_job(job_id)
        except JobLookupError:
            pass


@lru_cache
def get_apscheduler_gateway() -> APSchedulerGateway:
    return APSchedulerGateway()
