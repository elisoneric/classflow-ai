import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AuditEntityType
from app.infrastructure.db.session import get_db
from app.infrastructure.repositories.audit_log_repository import SqlAlchemyAuditLogWriter
from app.presentation.api.deps import get_current_user
from app.presentation.schemas.audit_logs import AuditLogResponse

router = APIRouter(
    prefix="/audit-logs", tags=["audit-logs"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    entity_type: AuditEntityType | None = None,
    entity_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
) -> list[AuditLogResponse]:
    repository = SqlAlchemyAuditLogWriter(session)
    logs = await repository.list_all(
        entity_type=entity_type, entity_id=entity_id, date_from=date_from, date_to=date_to
    )
    return [AuditLogResponse.model_validate(log) for log in logs]
