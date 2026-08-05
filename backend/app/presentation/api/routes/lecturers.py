import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.lecturers.service import LecturerService
from app.domain.exceptions import ConflictError, NotFoundError, UnsupportedContactMethodError
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.audit_log_repository import SqlAlchemyAuditLogWriter
from app.infrastructure.repositories.course_lecturer_repository import (
    SqlAlchemyCourseLecturerRepository,
)
from app.infrastructure.repositories.lecturer_repository import SqlAlchemyLecturerRepository
from app.presentation.api.deps import get_current_user
from app.presentation.schemas.lecturers import LecturerCreate, LecturerResponse, LecturerUpdate

router = APIRouter(
    prefix="/lecturers", tags=["lecturers"], dependencies=[Depends(get_current_user)]
)


def get_lecturer_service(session: AsyncSession = Depends(get_db)) -> LecturerService:
    return LecturerService(
        SqlAlchemyLecturerRepository(session),
        SqlAlchemyCourseLecturerRepository(session),
        SqlAlchemyAuditLogWriter(session),
        session,
    )


@router.get("", response_model=list[LecturerResponse])
async def list_lecturers(
    service: LecturerService = Depends(get_lecturer_service),
) -> list[LecturerResponse]:
    lecturers = await service.list_lecturers()
    return [LecturerResponse.model_validate(l) for l in lecturers]


@router.post("", response_model=LecturerResponse, status_code=status.HTTP_201_CREATED)
async def create_lecturer(
    payload: LecturerCreate,
    service: LecturerService = Depends(get_lecturer_service),
) -> LecturerResponse:
    try:
        lecturer = await service.create_lecturer(**payload.model_dump())
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except UnsupportedContactMethodError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return LecturerResponse.model_validate(lecturer)


@router.get("/{lecturer_id}", response_model=LecturerResponse)
async def get_lecturer(
    lecturer_id: uuid.UUID,
    service: LecturerService = Depends(get_lecturer_service),
) -> LecturerResponse:
    try:
        lecturer = await service.get_lecturer(lecturer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return LecturerResponse.model_validate(lecturer)


@router.patch("/{lecturer_id}", response_model=LecturerResponse)
async def update_lecturer(
    lecturer_id: uuid.UUID,
    payload: LecturerUpdate,
    service: LecturerService = Depends(get_lecturer_service),
) -> LecturerResponse:
    try:
        lecturer = await service.update_lecturer(
            lecturer_id, **payload.model_dump(exclude_unset=True)
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnsupportedContactMethodError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return LecturerResponse.model_validate(lecturer)


@router.delete("/{lecturer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lecturer(
    lecturer_id: uuid.UUID,
    service: LecturerService = Depends(get_lecturer_service),
) -> None:
    try:
        await service.delete_lecturer(lecturer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
