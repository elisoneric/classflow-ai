import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.common.ports import AuditLogWriter
from app.application.lecturers.ports import CourseLecturerRepository, LecturerRepository
from app.domain.enums import AuditActor, AuditEntityType, ContactMethod
from app.domain.exceptions import ConflictError, NotFoundError, UnsupportedContactMethodError
from app.infrastructure.db.models import CourseLecturer, Lecturer


class LecturerService:
    def __init__(
        self,
        lecturers: LecturerRepository,
        course_links: CourseLecturerRepository,
        audit: AuditLogWriter,
        session: AsyncSession,
    ):
        self._lecturers = lecturers
        self._course_links = course_links
        self._audit = audit
        self._session = session

    @staticmethod
    def _validate_contact_method(method: ContactMethod) -> None:
        if method == ContactMethod.WHATSAPP:
            raise UnsupportedContactMethodError(method.value)

    async def list_lecturers(self) -> list[Lecturer]:
        return await self._lecturers.list_all()

    async def list_course_links(self, course_id: uuid.UUID) -> list[CourseLecturer]:
        return await self._course_links.list_for_course(course_id)

    async def get_lecturer(self, lecturer_id: uuid.UUID) -> Lecturer:
        lecturer = await self._lecturers.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer", lecturer_id)
        return lecturer

    async def create_lecturer(
        self,
        *,
        name: str,
        email: str,
        phone: str | None,
        preferred_contact_method: ContactMethod,
        fallback_contact_method: ContactMethod,
    ) -> Lecturer:
        self._validate_contact_method(preferred_contact_method)
        self._validate_contact_method(fallback_contact_method)

        lecturer = Lecturer(
            name=name,
            email=email,
            phone=phone,
            preferred_contact_method=preferred_contact_method,
            fallback_contact_method=fallback_contact_method,
        )
        await self._lecturers.add(lecturer)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(f"Lecturer with email {email} already exists") from exc

        await self._audit.record(
            entity_type=AuditEntityType.LECTURER,
            entity_id=lecturer.id,
            action="LECTURER_CREATED",
            actor=AuditActor.COURSE_REP,
            new_state={"name": name, "email": email},
        )
        await self._session.commit()
        return lecturer

    async def update_lecturer(
        self,
        lecturer_id: uuid.UUID,
        *,
        name: str | None = None,
        phone: str | None = None,
        preferred_contact_method: ContactMethod | None = None,
        fallback_contact_method: ContactMethod | None = None,
    ) -> Lecturer:
        lecturer = await self.get_lecturer(lecturer_id)
        if preferred_contact_method is not None:
            self._validate_contact_method(preferred_contact_method)
        if fallback_contact_method is not None:
            self._validate_contact_method(fallback_contact_method)

        previous_state = {
            "name": lecturer.name,
            "phone": lecturer.phone,
            "preferred_contact_method": lecturer.preferred_contact_method.value,
            "fallback_contact_method": lecturer.fallback_contact_method.value,
        }
        if name is not None:
            lecturer.name = name
        if phone is not None:
            lecturer.phone = phone
        if preferred_contact_method is not None:
            lecturer.preferred_contact_method = preferred_contact_method
        if fallback_contact_method is not None:
            lecturer.fallback_contact_method = fallback_contact_method

        await self._audit.record(
            entity_type=AuditEntityType.LECTURER,
            entity_id=lecturer.id,
            action="LECTURER_UPDATED",
            actor=AuditActor.COURSE_REP,
            previous_state=previous_state,
            new_state={
                "name": lecturer.name,
                "phone": lecturer.phone,
                "preferred_contact_method": lecturer.preferred_contact_method.value,
                "fallback_contact_method": lecturer.fallback_contact_method.value,
            },
        )
        await self._session.commit()
        return lecturer

    async def delete_lecturer(self, lecturer_id: uuid.UUID) -> None:
        lecturer = await self.get_lecturer(lecturer_id)
        links = await self._course_links.list_for_lecturer(lecturer_id)
        if links:
            raise ConflictError(
                f"Cannot delete lecturer attached to {len(links)} course(s); detach first"
            )
        await self._lecturers.delete(lecturer)
        await self._audit.record(
            entity_type=AuditEntityType.LECTURER,
            entity_id=lecturer_id,
            action="LECTURER_DELETED",
            actor=AuditActor.COURSE_REP,
            previous_state={"name": lecturer.name, "email": lecturer.email},
        )
        await self._session.commit()

    async def attach_to_course(
        self, course_id: uuid.UUID, lecturer_id: uuid.UUID, *, is_primary: bool
    ) -> CourseLecturer:
        await self.get_lecturer(lecturer_id)  # 404s if missing
        existing = await self._course_links.get(course_id, lecturer_id)
        if existing is not None:
            raise ConflictError("Lecturer is already attached to this course")

        link = CourseLecturer(course_id=course_id, lecturer_id=lecturer_id, is_primary=is_primary)
        await self._course_links.add(link)
        await self._audit.record(
            entity_type=AuditEntityType.LECTURER,
            entity_id=lecturer_id,
            action="LECTURER_ATTACHED_TO_COURSE",
            actor=AuditActor.COURSE_REP,
            new_state={"course_id": str(course_id), "is_primary": is_primary},
        )
        await self._session.commit()
        return link

    async def detach_from_course(self, course_id: uuid.UUID, lecturer_id: uuid.UUID) -> None:
        link = await self._course_links.get(course_id, lecturer_id)
        if link is None:
            raise NotFoundError("CourseLecturer", f"{course_id}:{lecturer_id}")
        await self._course_links.delete(link)
        await self._audit.record(
            entity_type=AuditEntityType.LECTURER,
            entity_id=lecturer_id,
            action="LECTURER_DETACHED_FROM_COURSE",
            actor=AuditActor.COURSE_REP,
            previous_state={"course_id": str(course_id)},
        )
        await self._session.commit()
