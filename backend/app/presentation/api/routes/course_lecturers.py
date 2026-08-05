import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.lecturers.service import LecturerService
from app.domain.exceptions import ConflictError, NotFoundError
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.audit_log_repository import SqlAlchemyAuditLogWriter
from app.infrastructure.repositories.course_lecturer_repository import (
    SqlAlchemyCourseLecturerRepository,
)
from app.infrastructure.repositories.lecturer_repository import SqlAlchemyLecturerRepository
from app.presentation.api.deps import get_current_user
from app.presentation.schemas.lecturers import CourseLecturerAttach, CourseLecturerResponse

router = APIRouter(prefix="/courses", tags=["courses"], dependencies=[Depends(get_current_user)])


def get_lecturer_service(session: AsyncSession = Depends(get_db)) -> LecturerService:
    return LecturerService(
        SqlAlchemyLecturerRepository(session),
        SqlAlchemyCourseLecturerRepository(session),
        SqlAlchemyAuditLogWriter(session),
        session,
    )


@router.post(
    "/{course_id}/lecturers",
    response_model=CourseLecturerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_lecturer(
    course_id: uuid.UUID,
    payload: CourseLecturerAttach,
    service: LecturerService = Depends(get_lecturer_service),
) -> CourseLecturerResponse:
    try:
        link = await service.attach_to_course(
            course_id, payload.lecturer_id, is_primary=payload.is_primary
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return CourseLecturerResponse.model_validate(link)


@router.delete("/{course_id}/lecturers/{lecturer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_lecturer(
    course_id: uuid.UUID,
    lecturer_id: uuid.UUID,
    service: LecturerService = Depends(get_lecturer_service),
) -> None:
    try:
        await service.detach_from_course(course_id, lecturer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
