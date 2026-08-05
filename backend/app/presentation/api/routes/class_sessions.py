import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.class_sessions.service import ClassSessionService
from app.domain.enums import SessionStatus
from app.domain.exceptions import ConflictError, InvalidStateTransitionError, NotFoundError
from app.infrastructure.db.session import get_db
from app.infrastructure.notifications.smtp_email_channel import SmtpEmailChannel
from app.infrastructure.repositories.announcement_repository import (
    SqlAlchemyAnnouncementRepository,
)
from app.infrastructure.repositories.audit_log_repository import SqlAlchemyAuditLogWriter
from app.infrastructure.repositories.class_session_repository import (
    SqlAlchemyClassSessionRepository,
)
from app.infrastructure.repositories.course_lecturer_repository import (
    SqlAlchemyCourseLecturerRepository,
)
from app.infrastructure.repositories.course_repository import SqlAlchemyCourseRepository
from app.infrastructure.repositories.lecturer_repository import SqlAlchemyLecturerRepository
from app.infrastructure.repositories.reminder_repository import SqlAlchemyReminderRepository
from app.infrastructure.scheduler.noop_gateway import NoOpSchedulerGateway
from app.presentation.api.deps import get_current_user
from app.presentation.schemas.class_sessions import (
    ClassSessionDetailResponse,
    ClassSessionOverrideRequest,
    ClassSessionResponse,
    ReminderRead,
)

router = APIRouter(
    prefix="/class-sessions", tags=["class-sessions"], dependencies=[Depends(get_current_user)]
)


def get_class_session_service(session: AsyncSession = Depends(get_db)) -> ClassSessionService:
    return ClassSessionService(
        SqlAlchemyClassSessionRepository(session),
        SqlAlchemyReminderRepository(session),
        SqlAlchemyAnnouncementRepository(session),
        SqlAlchemyCourseRepository(session),
        SqlAlchemyLecturerRepository(session),
        SqlAlchemyCourseLecturerRepository(session),
        SmtpEmailChannel(),
        NoOpSchedulerGateway(),
        SqlAlchemyAuditLogWriter(session),
        session,
    )


@router.get("", response_model=list[ClassSessionResponse])
async def list_class_sessions(
    course_id: uuid.UUID | None = None,
    status_: SessionStatus | None = Query(None, alias="status"),
    date_from: date | None = None,
    date_to: date | None = None,
    service: ClassSessionService = Depends(get_class_session_service),
) -> list[ClassSessionResponse]:
    sessions = await service.list_sessions(
        course_id=course_id, status=status_, date_from=date_from, date_to=date_to
    )
    return [ClassSessionResponse.model_validate(s) for s in sessions]


@router.get("/{session_id}", response_model=ClassSessionDetailResponse)
async def get_class_session(
    session_id: uuid.UUID,
    service: ClassSessionService = Depends(get_class_session_service),
) -> ClassSessionDetailResponse:
    try:
        class_session = await service.get_session(session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ClassSessionDetailResponse.model_validate(class_session)


def _error_response(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, InvalidStateTransitionError | ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/{session_id}/override", response_model=ClassSessionResponse)
async def override_class_session(
    session_id: uuid.UUID,
    payload: ClassSessionOverrideRequest,
    service: ClassSessionService = Depends(get_class_session_service),
) -> ClassSessionResponse:
    try:
        class_session = await service.override(session_id, **payload.model_dump())
    except (NotFoundError, InvalidStateTransitionError, ConflictError) as exc:
        raise _error_response(exc) from exc
    return ClassSessionResponse.model_validate(class_session)


@router.post("/{session_id}/approve", response_model=ClassSessionResponse)
async def approve_class_session(
    session_id: uuid.UUID,
    service: ClassSessionService = Depends(get_class_session_service),
) -> ClassSessionResponse:
    try:
        class_session = await service.approve(session_id)
    except (NotFoundError, InvalidStateTransitionError, ConflictError) as exc:
        raise _error_response(exc) from exc
    return ClassSessionResponse.model_validate(class_session)


@router.post("/{session_id}/reject", response_model=ClassSessionResponse)
async def reject_class_session(
    session_id: uuid.UUID,
    payload: ClassSessionOverrideRequest,
    service: ClassSessionService = Depends(get_class_session_service),
) -> ClassSessionResponse:
    try:
        class_session = await service.reject(session_id, **payload.model_dump())
    except (NotFoundError, InvalidStateTransitionError, ConflictError) as exc:
        raise _error_response(exc) from exc
    return ClassSessionResponse.model_validate(class_session)


@router.post("/{session_id}/resend-reminder", response_model=ReminderRead)
async def resend_reminder(
    session_id: uuid.UUID,
    service: ClassSessionService = Depends(get_class_session_service),
) -> ReminderRead:
    try:
        reminder = await service.resend_reminder(session_id)
    except (NotFoundError, ConflictError) as exc:
        raise _error_response(exc) from exc
    return ReminderRead.model_validate(reminder)
