import uuid
from datetime import time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.common.ports import AuditLogWriter
from app.application.courses.ports import CourseRepository
from app.application.timetable.ports import TimetableSlotRepository
from app.domain.enums import AuditActor, AuditEntityType, ClassMode, ContactMethod, CourseStatus, DayOfWeek
from app.domain.exceptions import ConflictError, NotFoundError, ValidationError
from app.infrastructure.db.models import TimetableSlot


def _validate_timing(
    start_time: time,
    end_time: time,
    reminder_time: time,
    response_deadline_minutes: int,
    retry_attempts: int,
    retry_interval_minutes: int,
) -> None:
    if end_time <= start_time:
        raise ValidationError("end_time must be after start_time")
    if reminder_time > start_time:
        raise ValidationError("reminder_time must be at or before the class start_time")
    if response_deadline_minutes <= 0:
        raise ValidationError("response_deadline_minutes must be positive")
    if retry_attempts < 0:
        raise ValidationError("retry_attempts cannot be negative")
    if retry_attempts > 0 and retry_interval_minutes <= 0:
        raise ValidationError("retry_interval_minutes must be positive when retry_attempts > 0")


class TimetableSlotService:
    def __init__(
        self,
        slots: TimetableSlotRepository,
        courses: CourseRepository,
        audit: AuditLogWriter,
        session: AsyncSession,
    ):
        self._slots = slots
        self._courses = courses
        self._audit = audit
        self._session = session

    async def list_slots(self, course_id: uuid.UUID) -> list[TimetableSlot]:
        return await self._slots.list_for_course(course_id)

    async def get_slot(self, slot_id: uuid.UUID) -> TimetableSlot:
        slot = await self._slots.get_by_id(slot_id)
        if slot is None:
            raise NotFoundError("TimetableSlot", slot_id)
        return slot

    async def create_slot(
        self,
        course_id: uuid.UUID,
        *,
        day_of_week: DayOfWeek,
        start_time: time,
        end_time: time,
        venue: str,
        mode: ClassMode,
        reminder_time: time,
        response_deadline_minutes: int,
        retry_attempts: int,
        retry_interval_minutes: int,
        fallback_contact_method_override: ContactMethod | None = None,
    ) -> TimetableSlot:
        course = await self._courses.get_by_id(course_id)
        if course is None:
            raise NotFoundError("Course", course_id)
        if course.status == CourseStatus.COMPLETED:
            raise ConflictError("Cannot add a timetable slot to a completed course")

        _validate_timing(
            start_time, end_time, reminder_time, response_deadline_minutes,
            retry_attempts, retry_interval_minutes,
        )

        slot = TimetableSlot(
            course_id=course_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            venue=venue,
            mode=mode,
            reminder_time=reminder_time,
            response_deadline_minutes=response_deadline_minutes,
            retry_attempts=retry_attempts,
            retry_interval_minutes=retry_interval_minutes,
            fallback_contact_method_override=fallback_contact_method_override,
        )
        await self._slots.add(slot)
        await self._session.flush()
        await self._audit.record(
            entity_type=AuditEntityType.TIMETABLE_SLOT,
            entity_id=slot.id,
            action="TIMETABLE_SLOT_CREATED",
            actor=AuditActor.COURSE_REP,
            new_state={
                "course_id": str(course_id),
                "day_of_week": day_of_week.value,
                "start_time": str(start_time),
            },
        )
        await self._session.commit()
        return slot

    async def update_slot(self, slot_id: uuid.UUID, **fields) -> TimetableSlot:
        slot = await self.get_slot(slot_id)
        previous_state = {
            "start_time": str(slot.start_time),
            "end_time": str(slot.end_time),
            "reminder_time": str(slot.reminder_time),
            "venue": slot.venue,
            "is_active": slot.is_active,
        }

        merged = {
            "start_time": fields.get("start_time", slot.start_time),
            "end_time": fields.get("end_time", slot.end_time),
            "reminder_time": fields.get("reminder_time", slot.reminder_time),
            "response_deadline_minutes": fields.get(
                "response_deadline_minutes", slot.response_deadline_minutes
            ),
            "retry_attempts": fields.get("retry_attempts", slot.retry_attempts),
            "retry_interval_minutes": fields.get(
                "retry_interval_minutes", slot.retry_interval_minutes
            ),
        }
        _validate_timing(**merged)

        for field_name, value in fields.items():
            if value is not None:
                setattr(slot, field_name, value)

        await self._audit.record(
            entity_type=AuditEntityType.TIMETABLE_SLOT,
            entity_id=slot.id,
            action="TIMETABLE_SLOT_UPDATED",
            actor=AuditActor.COURSE_REP,
            previous_state=previous_state,
            new_state={
                "start_time": str(slot.start_time),
                "end_time": str(slot.end_time),
                "reminder_time": str(slot.reminder_time),
                "venue": slot.venue,
                "is_active": slot.is_active,
            },
        )
        await self._session.commit()
        return slot

    async def delete_slot(self, slot_id: uuid.UUID) -> None:
        slot = await self.get_slot(slot_id)
        try:
            await self._slots.delete(slot)
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(
                "Cannot delete a timetable slot with existing class sessions; "
                "set is_active=false instead"
            ) from exc

        await self._audit.record(
            entity_type=AuditEntityType.TIMETABLE_SLOT,
            entity_id=slot_id,
            action="TIMETABLE_SLOT_DELETED",
            actor=AuditActor.COURSE_REP,
            previous_state={"course_id": str(slot.course_id)},
        )
        await self._session.commit()
