import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.domain.enums import CourseStatus


class CourseCreate(BaseModel):
    semester_id: uuid.UUID
    code: str
    title: str
    announcement_email: EmailStr


class CourseUpdate(BaseModel):
    title: str | None = None
    announcement_email: EmailStr | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    semester_id: uuid.UUID
    code: str
    title: str
    status: CourseStatus
    announcement_email: str
