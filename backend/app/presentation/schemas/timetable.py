import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict

from app.domain.enums import ClassMode, ContactMethod, DayOfWeek


class TimetableSlotCreate(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    venue: str
    mode: ClassMode
    reminder_time: time
    response_deadline_minutes: int = 60
    retry_attempts: int = 1
    retry_interval_minutes: int = 30
    fallback_contact_method_override: ContactMethod | None = None


class TimetableSlotUpdate(BaseModel):
    day_of_week: DayOfWeek | None = None
    start_time: time | None = None
    end_time: time | None = None
    venue: str | None = None
    mode: ClassMode | None = None
    reminder_time: time | None = None
    response_deadline_minutes: int | None = None
    retry_attempts: int | None = None
    retry_interval_minutes: int | None = None
    fallback_contact_method_override: ContactMethod | None = None
    is_active: bool | None = None


class TimetableSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    venue: str
    mode: ClassMode
    reminder_time: time
    response_deadline_minutes: int
    retry_attempts: int
    retry_interval_minutes: int
    fallback_contact_method_override: ContactMethod | None
    is_active: bool
