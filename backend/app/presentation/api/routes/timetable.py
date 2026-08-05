import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.timetable.service import TimetableSlotService
from app.domain.exceptions import ConflictError, NotFoundError, ValidationError
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.audit_log_repository import SqlAlchemyAuditLogWriter
from app.infrastructure.repositories.course_repository import SqlAlchemyCourseRepository
from app.infrastructure.repositories.timetable_slot_repository import (
    SqlAlchemyTimetableSlotRepository,
)
from app.presentation.api.deps import get_current_user
from app.presentation.schemas.timetable import (
    TimetableSlotCreate,
    TimetableSlotResponse,
    TimetableSlotUpdate,
)

router = APIRouter(tags=["timetable"], dependencies=[Depends(get_current_user)])


def get_timetable_service(session: AsyncSession = Depends(get_db)) -> TimetableSlotService:
    return TimetableSlotService(
        SqlAlchemyTimetableSlotRepository(session),
        SqlAlchemyCourseRepository(session),
        SqlAlchemyAuditLogWriter(session),
        session,
    )


@router.get("/courses/{course_id}/timetable-slots", response_model=list[TimetableSlotResponse])
async def list_timetable_slots(
    course_id: uuid.UUID,
    service: TimetableSlotService = Depends(get_timetable_service),
) -> list[TimetableSlotResponse]:
    slots = await service.list_slots(course_id)
    return [TimetableSlotResponse.model_validate(s) for s in slots]


@router.post(
    "/courses/{course_id}/timetable-slots",
    response_model=TimetableSlotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_timetable_slot(
    course_id: uuid.UUID,
    payload: TimetableSlotCreate,
    service: TimetableSlotService = Depends(get_timetable_service),
) -> TimetableSlotResponse:
    try:
        slot = await service.create_slot(course_id, **payload.model_dump())
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ConflictError, ValidationError) as exc:
        code = (
            status.HTTP_409_CONFLICT
            if isinstance(exc, ConflictError)
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return TimetableSlotResponse.model_validate(slot)


@router.patch("/timetable-slots/{slot_id}", response_model=TimetableSlotResponse)
async def update_timetable_slot(
    slot_id: uuid.UUID,
    payload: TimetableSlotUpdate,
    service: TimetableSlotService = Depends(get_timetable_service),
) -> TimetableSlotResponse:
    try:
        slot = await service.update_slot(slot_id, **payload.model_dump(exclude_unset=True))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return TimetableSlotResponse.model_validate(slot)


@router.delete("/timetable-slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable_slot(
    slot_id: uuid.UUID,
    service: TimetableSlotService = Depends(get_timetable_service),
) -> None:
    try:
        await service.delete_slot(slot_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
