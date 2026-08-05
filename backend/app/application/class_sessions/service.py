import uuid
from datetime import UTC, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.class_sessions.ports import (
    AnnouncementRepository,
    ClassSessionRepository,
    LecturerResponseRepository,
    ReminderRepository,
)
from app.application.common.ports import AuditLogWriter
from app.application.courses.ports import CourseRepository
from app.application.lecturers.ports import CourseLecturerRepository, LecturerRepository
from app.application.timetable.ports import TimetableSlotRepository
from app.core.config import get_settings
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
from app.domain.value_objects import Interpretation, SessionContext
from app.infrastructure.db.models import Announcement, ClassSession, LecturerResponse, Reminder

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
        responses: LecturerResponseRepository,
        courses: CourseRepository,
        lecturers: LecturerRepository,
        course_lecturers: CourseLecturerRepository,
        timetable_slots: TimetableSlotRepository,
        notification_channel: NotificationChannel,
        scheduler: SchedulerGateway,
        audit: AuditLogWriter,
        session: AsyncSession,
    ):
        self._sessions = sessions
        self._reminders = reminders
        self._announcements = announcements
        self._responses = responses
        self._courses = courses
        self._lecturers = lecturers
        self._course_lecturers = course_lecturers
        self._timetable_slots = timetable_slots
        self._notification_channel = notification_channel
        self._scheduler = scheduler
        self._audit = audit
        self._session = session

    async def _get_primary_lecturer(self, course_id: uuid.UUID):
        links = await self._course_lecturers.list_for_course(course_id)
        primary = next((link for link in links if link.is_primary), None)
        if primary is None:
            return None
        return await self._lecturers.get_by_id(primary.lecturer_id)

    async def prepare_response_context(
        self, outbound_message_id: str
    ) -> tuple[Reminder, ClassSession, SessionContext] | None:
        """Looks up the reminder an inbound email is replying to (matched via
        Message-ID/In-Reply-To — see PROJECT.md §9/ADR-2) and builds the
        SessionContext the AI interpreter needs. Returns None if there's no
        matching pending reminder — either it's not a reply to us, or it's
        already been resolved by another path (duplicate reply, override).
        """
        reminder = await self._reminders.get_by_outbound_message_id(outbound_message_id)
        if reminder is None or reminder.status != ReminderStatus.SENT:
            return None

        class_session = await self.get_session(reminder.class_session_id)
        course = await self._courses.get_by_id(class_session.course_id)
        lecturer = await self._get_primary_lecturer(class_session.course_id)
        context = SessionContext(
            course_code=course.code if course else "",
            course_title=course.title if course else "",
            lecturer_name=lecturer.name if lecturer else "Lecturer",
            session_date=class_session.session_date.isoformat(),
            scheduled_start_time=class_session.scheduled_start_time.isoformat(timespec="minutes"),
            scheduled_venue=class_session.venue,
            scheduled_mode=class_session.mode,
        )
        return reminder, class_session, context

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

    async def _deliver_reminder(
        self, class_session: ClassSession, attempt_number: int, deadline_minutes: int
    ) -> tuple[Reminder, bool]:
        """Sends the reminder and records it as SENT regardless of delivery
        outcome — status=SENT tracks the attempt's place in the retry/deadline
        lifecycle, not literal SMTP success. A bounced/failed send still needs
        to flow through the normal deadline-check -> retry -> fallback path
        rather than getting silently stuck; the delivery outcome itself is
        only reflected in the audit log (`delivered`), not in `status`.
        EXPIRED is set exclusively by handle_deadline when the deadline
        actually passes.
        """
        course = await self._courses.get_by_id(class_session.course_id)
        if course is None:
            raise NotFoundError("Course", class_session.course_id)
        lecturer = await self._get_primary_lecturer(class_session.course_id)
        if lecturer is None:
            raise ConflictError("No primary lecturer assigned to this course")

        content = _format_reminder(course.code, course.title, class_session)
        result = await self._notification_channel.send(
            lecturer.email, f"{course.code} — class today?", content
        )

        now = datetime.now(UTC)
        reminder = Reminder(
            class_session_id=class_session.id,
            attempt_number=attempt_number,
            channel=NotificationChannelType.EMAIL,
            sent_at=now,
            deadline_at=now + timedelta(minutes=deadline_minutes),
            outbound_message_id=result.provider_message_id,
            status=ReminderStatus.SENT,
        )
        await self._reminders.add(reminder)
        await self._session.flush()
        class_session.status = SessionStatus.REMINDER_SENT
        return reminder, result.success

    async def resend_reminder(self, session_id: uuid.UUID) -> Reminder:
        class_session = await self.get_session(session_id)
        existing = await self._reminders.list_for_session(session_id)
        attempt_number = len(existing) + 1

        reminder, delivered = await self._deliver_reminder(
            class_session, attempt_number, DEFAULT_RESPONSE_DEADLINE_MINUTES
        )

        await self._audit.record(
            entity_type=AuditEntityType.REMINDER,
            entity_id=reminder.id,
            action="REMINDER_RESENT",
            actor=AuditActor.COURSE_REP,
            new_state={"attempt_number": attempt_number, "delivered": delivered},
        )
        await self._session.commit()
        return reminder

    async def send_scheduled_reminder(
        self, session_id: uuid.UUID, attempt_number: int
    ) -> Reminder:
        """System-triggered send — called by the RQ task an APScheduler date
        trigger enqueued (PROJECT.md §9, job #2). Schedules the matching
        deadline-check job so an unanswered reminder gets a retry or fallback.
        """
        class_session = await self.get_session(session_id)
        slot = (
            await self._timetable_slots.get_by_id(class_session.timetable_slot_id)
            if class_session.timetable_slot_id
            else None
        )
        deadline_minutes = slot.response_deadline_minutes if slot else DEFAULT_RESPONSE_DEADLINE_MINUTES

        reminder, delivered = await self._deliver_reminder(
            class_session, attempt_number, deadline_minutes
        )

        job_id = await self._scheduler.schedule_deadline_check(
            session_id, attempt_number, reminder.deadline_at
        )
        reminder.apscheduler_job_id = job_id

        await self._audit.record(
            entity_type=AuditEntityType.REMINDER,
            entity_id=reminder.id,
            action="REMINDER_SENT",
            actor=AuditActor.SYSTEM,
            new_state={"attempt_number": attempt_number, "delivered": delivered},
        )
        await self._session.commit()
        return reminder

    async def handle_deadline(self, session_id: uuid.UUID, attempt_number: int) -> None:
        """Called when a reminder's response deadline is reached (PROJECT.md §9,
        job #3). Always re-reads current state first — a response or manual
        override may have already resolved the session, in which case this
        is a no-op.
        """
        reminders = await self._reminders.list_for_session(session_id)
        reminder = next((r for r in reminders if r.attempt_number == attempt_number), None)
        if reminder is None or reminder.status != ReminderStatus.SENT:
            return

        class_session = await self.get_session(session_id)
        slot = (
            await self._timetable_slots.get_by_id(class_session.timetable_slot_id)
            if class_session.timetable_slot_id
            else None
        )
        retry_attempts = slot.retry_attempts if slot else 1
        retry_interval_minutes = slot.retry_interval_minutes if slot else 30

        reminder.status = ReminderStatus.EXPIRED

        if attempt_number <= retry_attempts:
            next_attempt = attempt_number + 1
            run_at = datetime.now(UTC) + timedelta(minutes=retry_interval_minutes)
            await self._scheduler.schedule_reminder(session_id, next_attempt, run_at)
            await self._audit.record(
                entity_type=AuditEntityType.REMINDER,
                entity_id=class_session.id,
                action="REMINDER_RETRY_SCHEDULED",
                actor=AuditActor.SYSTEM,
                new_state={"next_attempt": next_attempt, "run_at": run_at.isoformat()},
            )
            await self._session.commit()
            return

        class_session.status = SessionStatus.UNRESOLVED
        class_session.resolution_source = ResolutionSource.NO_RESPONSE_FALLBACK
        settings = get_settings()
        course = await self._courses.get_by_id(class_session.course_id)
        course_label = course.code if course else str(class_session.course_id)
        await self._notification_channel.send(
            settings.course_rep_email,
            f"{course_label} — no lecturer response",
            (
                f"No response received for {course_label} scheduled today "
                f"({class_session.session_date.isoformat()}). Please resolve manually "
                "from the dashboard."
            ),
        )
        await self._audit.record(
            entity_type=AuditEntityType.CLASS_SESSION,
            entity_id=class_session.id,
            action="CLASS_SESSION_UNRESOLVED",
            actor=AuditActor.SYSTEM,
            new_state={"status": SessionStatus.UNRESOLVED.value},
        )
        await self._session.commit()

    async def handle_lecturer_response(
        self,
        reminder_id: uuid.UUID,
        *,
        raw_message: str,
        cleaned_message: str,
        received_at: datetime,
        interpretation: Interpretation,
    ) -> ClassSession:
        """Called once IMAP polling + the AI interpreter have produced a
        structured reading of a lecturer's reply (PROJECT.md §11). Below the
        confidence threshold — or an explicit UNCLEAR — routes to
        PENDING_REVIEW (ADR-3) instead of auto-announcing.
        """
        reminder = await self._reminders.get_by_id(reminder_id)
        if reminder is None:
            raise NotFoundError("Reminder", reminder_id)
        class_session = await self.get_session(reminder.class_session_id)
        course = await self._courses.get_by_id(class_session.course_id)
        if course is None:
            raise NotFoundError("Course", class_session.course_id)

        settings = get_settings()
        requires_review = (
            interpretation.status == AIInterpretedStatus.UNCLEAR
            or interpretation.confidence < settings.ai_confidence_threshold
        )

        ai_new_time: time | None = None
        if interpretation.new_time:
            try:
                ai_new_time = datetime.strptime(interpretation.new_time, "%H:%M").time()
            except ValueError:
                ai_new_time = None

        response = LecturerResponse(
            reminder_id=reminder.id,
            class_session_id=class_session.id,
            raw_message=raw_message,
            cleaned_message=cleaned_message,
            received_at=received_at,
            ai_status=interpretation.status,
            ai_new_time=ai_new_time,
            ai_new_venue=interpretation.new_venue,
            ai_new_mode=interpretation.new_mode,
            ai_confidence=interpretation.confidence,
            ai_raw_output=interpretation.raw_output,
            requires_review=requires_review,
            model_name=interpretation.model_name,
            prompt_version=interpretation.prompt_version,
        )
        await self._responses.add(response)

        reminder.status = ReminderStatus.RESPONDED
        if reminder.apscheduler_job_id:
            await self._scheduler.cancel_job(reminder.apscheduler_job_id)
        await self._cancel_pending_reminders(class_session.id)

        if requires_review:
            class_session.status = SessionStatus.PENDING_REVIEW
            await self._notification_channel.send(
                settings.course_rep_email,
                f"{course.code} — review needed",
                (
                    f"A lecturer reply for {course.code} needs your review before it's "
                    f"announced.\n\nReply: {cleaned_message}\n\n"
                    f"AI read: {interpretation.status.value} "
                    f"(confidence {interpretation.confidence:.2f})\n"
                    f"Reasoning: {interpretation.reasoning}"
                ),
            )
            await self._audit.record(
                entity_type=AuditEntityType.CLASS_SESSION,
                entity_id=class_session.id,
                action="CLASS_SESSION_FLAGGED_FOR_REVIEW",
                actor=AuditActor.SYSTEM,
                new_state={
                    "ai_status": interpretation.status.value,
                    "confidence": interpretation.confidence,
                },
            )
            await self._session.commit()
            return class_session

        outcome = _AI_STATUS_TO_OUTCOME[interpretation.status]
        class_session.outcome = outcome
        class_session.final_venue = interpretation.new_venue or class_session.venue
        class_session.final_start_time = ai_new_time or class_session.scheduled_start_time
        class_session.final_mode = interpretation.new_mode or class_session.mode
        class_session.resolution_source = ResolutionSource.LECTURER_RESPONSE

        await self._send_announcement(course, class_session, None)

        await self._audit.record(
            entity_type=AuditEntityType.CLASS_SESSION,
            entity_id=class_session.id,
            action="CLASS_SESSION_AUTO_ANNOUNCED",
            actor=AuditActor.SYSTEM,
            new_state={
                "status": class_session.status.value,
                "outcome": outcome.value,
                "confidence": interpretation.confidence,
            },
        )
        await self._session.commit()
        return class_session
