import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.domain.enums import (
    AIInterpretedStatus,
    AnnouncementStatus,
    ClassMode,
    NotificationChannelType,
    ReminderStatus,
    ResolutionSource,
    SessionOutcome,
    SessionStatus,
)


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attempt_number: int
    channel: NotificationChannelType
    sent_at: datetime
    deadline_at: datetime
    status: ReminderStatus


class LecturerResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reminder_id: uuid.UUID
    raw_message: str
    cleaned_message: str
    received_at: datetime
    ai_status: AIInterpretedStatus | None
    ai_new_time: time | None
    ai_new_venue: str | None
    ai_new_mode: ClassMode | None
    ai_confidence: float | None
    requires_review: bool


class AnnouncementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: NotificationChannelType
    recipient: str
    content: str
    sent_at: datetime | None
    status: AnnouncementStatus | None


class ClassSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    timetable_slot_id: uuid.UUID | None
    session_date: date
    scheduled_start_time: time
    scheduled_end_time: time
    venue: str
    mode: ClassMode
    status: SessionStatus
    outcome: SessionOutcome | None
    final_start_time: time | None
    final_venue: str | None
    final_mode: ClassMode | None
    resolution_source: ResolutionSource
    announced_at: datetime | None


class ClassSessionDetailResponse(ClassSessionResponse):
    reminders: list[ReminderRead] = []
    responses: list[LecturerResponseRead] = []
    announcements: list[AnnouncementRead] = []


class ClassSessionOverrideRequest(BaseModel):
    outcome: SessionOutcome
    venue: str | None = None
    start_time: time | None = None
    mode: ClassMode | None = None
    note: str | None = None
