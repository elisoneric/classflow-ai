import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.domain.enums import ContactMethod


class LecturerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    preferred_contact_method: ContactMethod = ContactMethod.EMAIL
    fallback_contact_method: ContactMethod = ContactMethod.EMAIL


class LecturerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    preferred_contact_method: ContactMethod | None = None
    fallback_contact_method: ContactMethod | None = None


class LecturerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    preferred_contact_method: ContactMethod
    fallback_contact_method: ContactMethod


class CourseLecturerAttach(BaseModel):
    lecturer_id: uuid.UUID
    is_primary: bool = True


class CourseLecturerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: uuid.UUID
    lecturer_id: uuid.UUID
    is_primary: bool
