"""Fakes for the ports each service depends on — matches PROJECT.md §15:
"NotificationChannel and MessageInterpreter are trivially fakeable via their
ports." Used for unit tests that exercise business logic with no DB/network.
"""

from app.domain.value_objects import DeliveryResult, Interpretation


class FakeAuditLogWriter:
    def __init__(self):
        self.records: list[dict] = []

    async def record(self, **kwargs) -> None:
        self.records.append(kwargs)


class FakeAsyncSession:
    """Stands in for AsyncSession where a service only needs flush/commit/
    rollback as lifecycle no-ops — real persistence is exercised separately
    by the integration tests.
    """

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


class FakeNotificationChannel:
    def __init__(self, succeed: bool = True):
        self.succeed = succeed
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> DeliveryResult:
        self.sent.append((to, subject, body))
        if self.succeed:
            return DeliveryResult(success=True, provider_message_id="<fake@test>")
        return DeliveryResult(success=False, error="fake failure")


class FakeSchedulerGateway:
    def __init__(self):
        self.scheduled_reminders: list[tuple] = []
        self.scheduled_deadlines: list[tuple] = []
        self.cancelled: list[str] = []

    async def schedule_reminder(self, class_session_id, attempt_number, run_at) -> str:
        job_id = f"send-reminder-{class_session_id}-{attempt_number}"
        self.scheduled_reminders.append((class_session_id, attempt_number, run_at))
        return job_id

    async def schedule_deadline_check(self, class_session_id, attempt_number, run_at) -> str:
        job_id = f"check-deadline-{class_session_id}-{attempt_number}"
        self.scheduled_deadlines.append((class_session_id, attempt_number, run_at))
        return job_id

    async def cancel_job(self, job_id: str) -> None:
        self.cancelled.append(job_id)


class FakeMessageInterpreter:
    def __init__(self, interpretation: Interpretation):
        self.interpretation = interpretation
        self.calls: list[tuple[str, object]] = []

    async def interpret(self, raw_message: str, context) -> Interpretation:
        self.calls.append((raw_message, context))
        return self.interpretation
