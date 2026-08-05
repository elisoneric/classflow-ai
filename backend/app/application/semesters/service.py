import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.common.ports import AuditLogWriter
from app.application.semesters.ports import SemesterRepository
from app.domain.enums import AuditActor, AuditEntityType
from app.domain.exceptions import NotFoundError
from app.infrastructure.db.models import Semester


class SemesterService:
    def __init__(
        self,
        repository: SemesterRepository,
        audit: AuditLogWriter,
        session: AsyncSession,
    ):
        self._repository = repository
        self._audit = audit
        self._session = session

    async def list_semesters(self) -> list[Semester]:
        return await self._repository.list_all()

    async def create_semester(
        self, *, name: str, start_date: date, end_date: date, timezone: str
    ) -> Semester:
        semester = Semester(name=name, start_date=start_date, end_date=end_date, timezone=timezone)
        await self._repository.add(semester)
        await self._session.flush()
        await self._audit.record(
            entity_type=AuditEntityType.SEMESTER,
            entity_id=semester.id,
            action="SEMESTER_CREATED",
            actor=AuditActor.COURSE_REP,
            new_state={"name": name, "start_date": str(start_date), "end_date": str(end_date)},
        )
        await self._session.commit()
        return semester

    async def update_semester(
        self,
        semester_id: uuid.UUID,
        *,
        name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        timezone: str | None = None,
    ) -> Semester:
        semester = await self._repository.get_by_id(semester_id)
        if semester is None:
            raise NotFoundError("Semester", semester_id)

        previous_state = {
            "name": semester.name,
            "start_date": str(semester.start_date),
            "end_date": str(semester.end_date),
            "timezone": semester.timezone,
        }
        if name is not None:
            semester.name = name
        if start_date is not None:
            semester.start_date = start_date
        if end_date is not None:
            semester.end_date = end_date
        if timezone is not None:
            semester.timezone = timezone

        await self._audit.record(
            entity_type=AuditEntityType.SEMESTER,
            entity_id=semester.id,
            action="SEMESTER_UPDATED",
            actor=AuditActor.COURSE_REP,
            previous_state=previous_state,
            new_state={
                "name": semester.name,
                "start_date": str(semester.start_date),
                "end_date": str(semester.end_date),
                "timezone": semester.timezone,
            },
        )
        await self._session.commit()
        return semester

    async def activate_semester(self, semester_id: uuid.UUID) -> Semester:
        semesters = await self._repository.list_all()
        target = next((s for s in semesters if s.id == semester_id), None)
        if target is None:
            raise NotFoundError("Semester", semester_id)

        for semester in semesters:
            semester.is_active = semester.id == semester_id

        await self._audit.record(
            entity_type=AuditEntityType.SEMESTER,
            entity_id=target.id,
            action="SEMESTER_ACTIVATED",
            actor=AuditActor.COURSE_REP,
            new_state={"id": str(target.id), "name": target.name},
        )
        await self._session.commit()
        return target
