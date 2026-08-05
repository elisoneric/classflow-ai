import uuid
from datetime import datetime

from app.infrastructure.scheduler.job_ids import check_deadline_job_id, send_reminder_job_id


class NoOpSchedulerGateway:
    """Fake SchedulerGateway for tests and for any code path exercised before
    the real APSchedulerGateway is wired up. Scheduling just returns the job
    id it would have used; cancelling is always a no-op.
    """

    async def schedule_reminder(
        self, class_session_id: uuid.UUID, attempt_number: int, run_at: datetime
    ) -> str:
        return send_reminder_job_id(class_session_id, attempt_number)

    async def schedule_deadline_check(
        self, class_session_id: uuid.UUID, attempt_number: int, run_at: datetime
    ) -> str:
        return check_deadline_job_id(class_session_id, attempt_number)

    async def cancel_job(self, job_id: str) -> None:
        return None
