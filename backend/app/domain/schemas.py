from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import time, date, datetime
from app.domain.models import CourseStatus, SessionStatus, ContactMethod

# --- Auth & User ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}

# --- Lecturer ---
class LecturerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    preferred_contact: ContactMethod = ContactMethod.EMAIL
    fallback_contact: ContactMethod = ContactMethod.EMAIL

class LecturerCreate(LecturerBase):
    pass

class LecturerResponse(LecturerBase):
    id: int

    model_config = {"from_attributes": True}

# --- Course ---
class CourseBase(BaseModel):
    code: str
    name: str
    status: CourseStatus = CourseStatus.ACTIVE
    lecturer_id: Optional[int] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    lecturer: Optional[LecturerResponse] = None

    model_config = {"from_attributes": True}

# --- Timetable ---
class TimetableBase(BaseModel):
    course_id: int
    day_of_week: int
    start_time: time
    end_time: time
    venue: str
    reminder_offset_minutes: int = 120
    deadline_offset_minutes: int = 30

class TimetableCreate(TimetableBase):
    pass

class TimetableResponse(TimetableBase):
    id: int
    course: Optional[CourseResponse] = None

    model_config = {"from_attributes": True}

# --- ClassSession ---
class ClassSessionBase(BaseModel):
    timetable_id: int
    date: date
    status: SessionStatus = SessionStatus.SCHEDULED
    lecturer_response: Optional[str] = None
    actual_time: Optional[time] = None
    actual_venue: Optional[str] = None
    actual_mode: Optional[str] = None

class ClassSessionCreate(ClassSessionBase):
    pass

class ClassSessionResponse(ClassSessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    timetable: Optional[TimetableResponse] = None

    model_config = {"from_attributes": True}
