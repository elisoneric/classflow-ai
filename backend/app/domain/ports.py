"""
Interfaces the application layer depends on. Infrastructure provides the
implementations (adapters). See PROJECT.md §10 (notifications) and §11 (AI).

Repository protocols are declared per-feature in each feature's service module
rather than centralized here — see app/application/<feature>/ports.py — so
each slice only depends on the query shapes it actually needs.
"""

import uuid
from datetime import datetime
from typing import Protocol

from app.domain.value_objects import DeliveryResult, Interpretation, SessionContext


class NotificationChannel(Protocol):
    async def send(self, to: str, subject: str, body: str) -> DeliveryResult: ...


class MessageInterpreter(Protocol):
    async def interpret(
        self, raw_message: str, context: SessionContext
    ) -> Interpretation: ...


class SchedulerGateway(Protocol):
    """Lets the application layer schedule/cancel APScheduler jobs without
    depending on APScheduler directly. See PROJECT.md §9. Job IDs are
    deterministic (f"send-reminder-{session_id}-{attempt}" and
    f"check-deadline-{session_id}-{attempt}") so a session can be cancelled
    even before the Reminder row for its next attempt exists yet.
    """

    async def schedule_reminder(
        self, class_session_id: uuid.UUID, attempt_number: int, run_at: datetime
    ) -> str: ...

    async def schedule_deadline_check(
        self, class_session_id: uuid.UUID, attempt_number: int, run_at: datetime
    ) -> str: ...

    async def cancel_job(self, job_id: str) -> None: ...
