import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.common.ports import AuditLogWriter
from app.application.courses.ports import CourseRepository
from app.domain.enums import AuditActor, AuditEntityType, CourseStatus
from app.domain.exceptions import InvalidStateTransitionError, NotFoundError
from app.infrastructure.db.models import Course

_VALID_TRANSITIONS: dict[CourseStatus, set[CourseStatus]] = {
    CourseStatus.ACTIVE: {CourseStatus.PAUSED, CourseStatus.COMPLETED},
    CourseStatus.PAUSED: {CourseStatus.ACTIVE, CourseStatus.COMPLETED},
    CourseStatus.COMPLETED: set(),  # terminal — history remains available, no further transitions
}


class CourseService:
    def __init__(
        self,
        repository: CourseRepository,
        audit: AuditLogWriter,
        session: AsyncSession,
    ):
        self._repository = repository
        self._audit = audit
        self._session = session

    async def list_courses(self, *, semester_id: uuid.UUID | None = None) -> list[Course]:
        return await self._repository.list_all(semester_id=semester_id)

    async def get_course(self, course_id: uuid.UUID) -> Course:
        course = await self._repository.get_by_id(course_id)
        if course is None:
            raise NotFoundError("Course", course_id)
        return course

    async def create_course(
        self,
        *,
        semester_id: uuid.UUID,
        code: str,
        title: str,
        announcement_email: str,
    ) -> Course:
        course = Course(
            semester_id=semester_id,
            code=code,
            title=title,
            announcement_email=announcement_email,
            status=CourseStatus.ACTIVE,
        )
        await self._repository.add(course)
        await self._session.flush()
        await self._audit.record(
            entity_type=AuditEntityType.COURSE,
            entity_id=course.id,
            action="COURSE_CREATED",
            actor=AuditActor.COURSE_REP,
            new_state={"code": code, "title": title},
        )
        await self._session.commit()
        return course

    async def update_course(
        self,
        course_id: uuid.UUID,
        *,
        title: str | None = None,
        announcement_email: str | None = None,
    ) -> Course:
        course = await self.get_course(course_id)
        previous_state = {"title": course.title, "announcement_email": course.announcement_email}
        if title is not None:
            course.title = title
        if announcement_email is not None:
            course.announcement_email = announcement_email

        await self._audit.record(
            entity_type=AuditEntityType.COURSE,
            entity_id=course.id,
            action="COURSE_UPDATED",
            actor=AuditActor.COURSE_REP,
            previous_state=previous_state,
            new_state={"title": course.title, "announcement_email": course.announcement_email},
        )
        await self._session.commit()
        return course

    async def _transition(self, course_id: uuid.UUID, target: CourseStatus) -> Course:
        course = await self.get_course(course_id)
        if target not in _VALID_TRANSITIONS[course.status]:
            raise InvalidStateTransitionError(
                "Course", course.status.value, f"transition to {target.value}"
            )
        previous_status = course.status
        course.status = target
        await self._audit.record(
            entity_type=AuditEntityType.COURSE,
            entity_id=course.id,
            action=f"COURSE_{target.value}",
            actor=AuditActor.COURSE_REP,
            previous_state={"status": previous_status.value},
            new_state={"status": target.value},
        )
        await self._session.commit()
        return course

    async def pause_course(self, course_id: uuid.UUID) -> Course:
        return await self._transition(course_id, CourseStatus.PAUSED)

    async def resume_course(self, course_id: uuid.UUID) -> Course:
        return await self._transition(course_id, CourseStatus.ACTIVE)

    async def complete_course(self, course_id: uuid.UUID) -> Course:
        return await self._transition(course_id, CourseStatus.COMPLETED)
