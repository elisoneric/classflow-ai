import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class SemesterCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    timezone: str = "Africa/Lagos"


class SemesterUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    timezone: str | None = None


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    timezone: str
    is_active: bool
