import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.courses.service import CourseService
from app.domain.exceptions import InvalidStateTransitionError, NotFoundError
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.audit_log_repository import SqlAlchemyAuditLogWriter
from app.infrastructure.repositories.course_repository import SqlAlchemyCourseRepository
from app.presentation.api.deps import get_current_user
from app.presentation.schemas.courses import CourseCreate, CourseResponse, CourseUpdate

router = APIRouter(prefix="/courses", tags=["courses"], dependencies=[Depends(get_current_user)])


def get_course_service(session: AsyncSession = Depends(get_db)) -> CourseService:
    return CourseService(
        SqlAlchemyCourseRepository(session), SqlAlchemyAuditLogWriter(session), session
    )


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    semester_id: uuid.UUID | None = None,
    service: CourseService = Depends(get_course_service),
) -> list[CourseResponse]:
    courses = await service.list_courses(semester_id=semester_id)
    return [CourseResponse.model_validate(c) for c in courses]


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    course = await service.create_course(
        semester_id=payload.semester_id,
        code=payload.code,
        title=payload.title,
        announcement_email=payload.announcement_email,
    )
    return CourseResponse.model_validate(course)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: uuid.UUID,
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    try:
        course = await service.get_course(course_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    try:
        course = await service.update_course(course_id, **payload.model_dump(exclude_unset=True))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CourseResponse.model_validate(course)


async def _transition_or_error(coro) -> CourseResponse:
    try:
        course = await coro
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return CourseResponse.model_validate(course)


@router.post("/{course_id}/pause", response_model=CourseResponse)
async def pause_course(
    course_id: uuid.UUID, service: CourseService = Depends(get_course_service)
) -> CourseResponse:
    return await _transition_or_error(service.pause_course(course_id))


@router.post("/{course_id}/resume", response_model=CourseResponse)
async def resume_course(
    course_id: uuid.UUID, service: CourseService = Depends(get_course_service)
) -> CourseResponse:
    return await _transition_or_error(service.resume_course(course_id))


@router.post("/{course_id}/complete", response_model=CourseResponse)
async def complete_course(
    course_id: uuid.UUID, service: CourseService = Depends(get_course_service)
) -> CourseResponse:
    return await _transition_or_error(service.complete_course(course_id))
