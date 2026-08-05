import uuid
from datetime import UTC, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.class_sessions.ports import (
    AnnouncementRepository,
    ClassSessionRepository,
    ReminderRepository,
)
from app.application.common.ports import AuditLogWriter
from app.application.courses.ports import CourseRepository
from app.application.lecturers.ports import CourseLecturerRepository, LecturerRepository
from app.domain.enums import (
    AIInterpretedStatus,
    AnnouncementStatus,
    AuditActor,
    AuditEntityType,
    ClassMode,
    NotificationChannelType,
    ReminderStatus,
    ResolutionSource,
    SessionOutcome,
    SessionStatus,
)
from app.domain.exceptions import ConflictError, InvalidStateTransitionError, NotFoundError
from app.domain.ports import NotificationChannel, SchedulerGateway
from app.infrastructure.db.models import Announcement, ClassSession, Reminder

DEFAULT_RESPONSE_DEADLINE_MINUTES = 60

_AI_STATUS_TO_OUTCOME: dict[AIInterpretedStatus, SessionOutcome] = {
    AIInterpretedStatus.CONFIRMED: SessionOutcome.CONFIRMED,
    AIInterpretedStatus.CANCELLED: SessionOutcome.CANCELLED,
    AIInterpretedStatus.DELAYED: SessionOutcome.DELAYED,
    AIInterpretedStatus.RELOCATED: SessionOutcome.RELOCATED,
    AIInterpretedStatus.ONLINE: SessionOutcome.ONLINE,
}


def _format_announcement(
    course_code: str, course_title: str, session: ClassSession, note: str | None
) -> str:
    outcome_label = session.outcome.value if session.outcome else "UNKNOWN"
    lines = [
        f"{course_code} — {course_title}",
        f"Date: {session.session_date.isoformat()}",
        f"Status: {outcome_label}",
    ]
    if session.outcome == SessionOutcome.DELAYED and session.final_start_time:
        lines.append(f"New time: {session.final_start_time.isoformat(timespec='minutes')}")
    if session.outcome == SessionOutcome.RELOCATED and session.final_venue:
        lines.append(f"New venue: {session.final_venue}")
    if session.outcome == SessionOutcome.ONLINE:
        lines.append("Mode: Online")
    if note:
        lines.append(f"Note: {note}")
    return "\n".join(lines)


def _format_reminder(course_code: str, course_title: str, session: ClassSession) -> str:
    return (
        f"Hi, is {course_code} ({course_title}) holding today "
        f"({session.session_date.isoformat()}) at "
        f"{session.scheduled_start_time.isoformat(timespec='minutes')} in {session.venue}?\n\n"
        'Please reply to confirm, cancel, delay, relocate, or move online — '
        'just reply naturally, e.g. "No class today" or "We\'ll start by 5:30".'
    )


class ClassSessionService:
    def __init__(
        self,
        sessions: ClassSessionRepository,
        reminders: ReminderRepository,
        announcements: AnnouncementRepository,
        courses: CourseRepository,
        lecturers: LecturerRepository,
        course_lecturers: CourseLecturerRepository,
        notification_channel: NotificationChannel,
        scheduler: SchedulerGateway,
        audit: AuditLogWriter,
        session: AsyncSession,
    ):
        self._sessions = sessions
        self._reminders = reminders
        self._announcements = announcements
        self._courses = courses
        self._lecturers = lecturers
        self._course_lecturers = course_lecturers
        self._notification_channel = notification_channel
        self._scheduler = scheduler
        self._audit = audit
        self._session = session

    async def list_sessions(self, **filters) -> list[ClassSession]:
        return await self._sessions.list_all(**filters)

    async def get_session(self, session_id: uuid.UUID) -> ClassSession:
        class_session = await self._sessions.get_by_id(session_id)
        if class_session is None:
            raise NotFoundError("ClassSession", session_id)
        return class_session

    async def _cancel_pending_reminders(self, class_session_id: uuid.UUID) -> None:
        pending = await self._reminders.list_pending_for_session(class_session_id)
        for reminder in pending:
            reminder.status = ReminderStatus.CANCELLED
            if reminder.apscheduler_job_id:
                await self._scheduler.cancel_job(reminder.apscheduler_job_id)

    async def _send_announcement(
        self, course, class_session: ClassSession, note: str | None
    ) -> None:
        content = _format_announcement(course.code, course.title, class_session, note)
        result = await self._notification_channel.send(
            course.announcement_email, f"{course.code} class update", content
        )
        announcement = Announcement(
            class_session_id=class_session.id,
            channel=NotificationChannelType.EMAIL,
            recipient=course.announcement_email,
            content=content,
            sent_at=datetime.now(UTC) if result.success else None,
            status=AnnouncementStatus.SENT if result.success else AnnouncementStatus.FAILED,
        )
        await self._announcements.add(announcement)
        class_session.announced_at = datetime.now(UTC)
        class_session.status = SessionStatus.ANNOUNCED

    async def override(
        self,
        session_id: uuid.UUID,
        *,
        outcome: SessionOutcome,
        venue: str | None = None,
        start_time: time | None = None,
        mode: ClassMode | None = None,
        note: str | None = None,
    ) -> ClassSession:
        class_session = await self.get_session(session_id)
        course = await self._courses.get_by_id(class_session.course_id)
        if course is None:
            raise NotFoundError("Course", class_session.course_id)

        previous_state = {
            "status": class_session.status.value,
            "outcome": class_session.outcome.value if class_session.outcome else None,
        }

        await self._cancel_pending_reminders(session_id)

        class_session.outcome = outcome
        class_session.final_venue = venue or class_session.venue
        class_session.final_start_time = start_time or class_session.scheduled_start_time
        class_session.final_mode = mode or class_session.mode
        class_session.resolution_source = ResolutionSource.MANUAL_OVERRIDE

        await self._send_announcement(course, class_session, note)

        await self._audit.record(
            entity_type=AuditEntityType.CLASS_SESSION,
            entity_id=class_session.id,
            action="CLASS_SESSION_OVERRIDDEN",
            actor=AuditActor.COURSE_REP,
            previous_state=previous_state,
            new_state={"status": class_session.status.value, "outcome": outcome.value},
            note=note,
        )
        await self._session.commit()
        return class_session

    async def approve(self, session_id: uuid.UUID) -> ClassSession:
        class_session = await self.get_session(session_id)
        if class_session.status != SessionStatus.PENDING_REVIEW:
            raise InvalidStateTransitionError(
                "ClassSession", class_session.status.value, "approve"
            )

        course = await self._courses.get_by_id(class_session.course_id)
        if course is None:
            raise NotFoundError("Course", class_session.course_id)

        latest_response = max(
            class_session.responses, key=lambda r: r.received_at, default=None
        )
        if latest_response is None or latest_response.ai_status is None:
            raise ConflictError("No AI interpretation available to approve")

        outcome = _AI_STATUS_TO_OUTCOME.get(latest_response.ai_status)
        if outcome is None:
            raise ConflictError("AI interpretation was UNCLEAR; use override instead")

        previous_state = {"status": class_session.status.value}
        await self._cancel_pending_reminders(session_id)

        class_session.outcome = outcome
        class_session.final_venue = latest_response.ai_new_venue or class_session.venue
        class_session.final_start_time = (
            latest_response.ai_new_time or class_session.scheduled_start_time
        )
        class_session.final_mode = latest_response.ai_new_mode or class_session.mode
        class_session.resolution_source = ResolutionSource.LECTURER_RESPONSE

        await self._send_announcement(course, class_session, None)

        await self._audit.record(
            entity_type=AuditEntityType.CLASS_SESSION,
            entity_id=class_session.id,
            action="CLASS_SESSION_APPROVED",
            actor=AuditActor.COURSE_REP,
            previous_state=previous_state,
            new_state={"status": class_session.status.value, "outcome": outcome.value},
        )
        await self._session.commit()
        return class_session

    async def reject(
        self,
        session_id: uuid.UUID,
        *,
        outcome: SessionOutcome,
        venue: str | None = None,
        start_time: time | None = None,
        mode: ClassMode | None = None,
        note: str | None = None,
    ) -> ClassSession:
        class_session = await self.get_session(session_id)
        if class_session.status != SessionStatus.PENDING_REVIEW:
            raise InvalidStateTransitionError("ClassSession", class_session.status.value, "reject")
        return await self.override(
            session_id,
            outcome=outcome,
            venue=venue,
            start_time=start_time,
            mode=mode,
            note=note or "AI interpretation rejected — corrected manually",
        )

    async def resend_reminder(self, session_id: uuid.UUID) -> Reminder:
        class_session = await self.get_session(session_id)
        course = await self._courses.get_by_id(class_session.course_id)
        if course is None:
            raise NotFoundError("Course", class_session.course_id)

        links = await self._course_lecturers.list_for_course(class_session.course_id)
        primary = next((link for link in links if link.is_primary), None)
        if primary is None:
            raise ConflictError("No primary lecturer assigned to this course")
        lecturer = await self._lecturers.get_by_id(primary.lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer", primary.lecturer_id)

        existing = await self._reminders.list_for_session(session_id)
        attempt_number = len(existing) + 1

        content = _format_reminder(course.code, course.title, class_session)
        result = await self._notification_channel.send(
            lecturer.email, f"{course.code} — class today?", content
        )

        now = datetime.now(UTC)
        reminder = Reminder(
            class_session_id=session_id,
            attempt_number=attempt_number,
            channel=NotificationChannelType.EMAIL,
            sent_at=now,
            deadline_at=now + timedelta(minutes=DEFAULT_RESPONSE_DEADLINE_MINUTES),
            outbound_message_id=result.provider_message_id,
            status=ReminderStatus.SENT if result.success else ReminderStatus.EXPIRED,
        )
        await self._reminders.add(reminder)
        await self._session.flush()
        class_session.status = SessionStatus.REMINDER_SENT

        await self._audit.record(
            entity_type=AuditEntityType.REMINDER,
            entity_id=reminder.id,
            action="REMINDER_RESENT",
            actor=AuditActor.COURSE_REP,
            new_state={"attempt_number": attempt_number, "delivered": result.success},
        )
        await self._session.commit()
        return reminder
