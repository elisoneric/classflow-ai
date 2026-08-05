import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.semesters.service import SemesterService
from app.domain.exceptions import NotFoundError
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.audit_log_repository import SqlAlchemyAuditLogWriter
from app.infrastructure.repositories.semester_repository import SqlAlchemySemesterRepository
from app.presentation.api.deps import get_current_user
from app.presentation.schemas.semesters import SemesterCreate, SemesterResponse, SemesterUpdate

router = APIRouter(
    prefix="/semesters", tags=["semesters"], dependencies=[Depends(get_current_user)]
)


def get_semester_service(session: AsyncSession = Depends(get_db)) -> SemesterService:
    return SemesterService(
        SqlAlchemySemesterRepository(session), SqlAlchemyAuditLogWriter(session), session
    )


@router.get("", response_model=list[SemesterResponse])
async def list_semesters(
    service: SemesterService = Depends(get_semester_service),
) -> list[SemesterResponse]:
    semesters = await service.list_semesters()
    return [SemesterResponse.model_validate(s) for s in semesters]


@router.post("", response_model=SemesterResponse, status_code=status.HTTP_201_CREATED)
async def create_semester(
    payload: SemesterCreate,
    service: SemesterService = Depends(get_semester_service),
) -> SemesterResponse:
    semester = await service.create_semester(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        timezone=payload.timezone,
    )
    return SemesterResponse.model_validate(semester)


@router.patch("/{semester_id}", response_model=SemesterResponse)
async def update_semester(
    semester_id: uuid.UUID,
    payload: SemesterUpdate,
    service: SemesterService = Depends(get_semester_service),
) -> SemesterResponse:
    try:
        semester = await service.update_semester(semester_id, **payload.model_dump(exclude_unset=True))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SemesterResponse.model_validate(semester)


@router.post("/{semester_id}/activate", response_model=SemesterResponse)
async def activate_semester(
    semester_id: uuid.UUID,
    service: SemesterService = Depends(get_semester_service),
) -> SemesterResponse:
    try:
        semester = await service.activate_semester(semester_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SemesterResponse.model_validate(semester)
