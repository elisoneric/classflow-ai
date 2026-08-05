import uuid

import pytest

from app.application.courses.service import CourseService
from app.domain.enums import CourseStatus
from app.domain.exceptions import InvalidStateTransitionError, NotFoundError
from app.infrastructure.db.models import Course
from tests.unit.fakes import FakeAsyncSession, FakeAuditLogWriter


class FakeCourseRepository:
    def __init__(self):
        self.courses: dict[uuid.UUID, Course] = {}

    async def list_all(self, *, semester_id=None):
        return [
            c for c in self.courses.values() if semester_id is None or c.semester_id == semester_id
        ]

    async def get_by_id(self, course_id):
        return self.courses.get(course_id)

    async def add(self, course):
        course.id = course.id or uuid.uuid4()
        self.courses[course.id] = course


@pytest.fixture
def audit():
    return FakeAuditLogWriter()


@pytest.fixture
def service(audit):
    return CourseService(FakeCourseRepository(), audit, FakeAsyncSession())


async def _make_course(service: CourseService, code: str = "CSC803") -> Course:
    return await service.create_course(
        semester_id=uuid.uuid4(), code=code, title="Advanced Analysis of Algorithms",
        announcement_email="class@example.com",
    )


async def test_create_course_defaults_to_active(service):
    course = await _make_course(service)
    assert course.status == CourseStatus.ACTIVE


async def test_pause_then_resume_round_trip(service):
    course = await _make_course(service)
    paused = await service.pause_course(course.id)
    assert paused.status == CourseStatus.PAUSED
    resumed = await service.resume_course(course.id)
    assert resumed.status == CourseStatus.ACTIVE


@pytest.mark.parametrize("path", ["pause_course", "resume_course", "complete_course"])
async def test_completed_is_a_terminal_state(service, path):
    course = await _make_course(service)
    await service.complete_course(course.id)
    with pytest.raises(InvalidStateTransitionError):
        await getattr(service, path)(course.id)


async def test_get_unknown_course_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.get_course(uuid.uuid4())


async def test_audit_log_written_on_every_transition(service, audit):
    course = await _make_course(service)
    await service.pause_course(course.id)
    actions = [r["action"] for r in audit.records]
    assert actions == ["COURSE_CREATED", "COURSE_PAUSED"]
