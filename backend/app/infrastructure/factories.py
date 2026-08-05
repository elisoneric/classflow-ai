"""
Shared DI wiring for ClassSessionService — used by both the API router
(app/presentation/api/routes/class_sessions.py) and the RQ task functions
(app/infrastructure/jobs/tasks.py) so the two call sites can't drift apart.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.class_sessions.service import ClassSessionService
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
from app.infrastructure.repositories.lecturer_response_repository import (
    SqlAlchemyLecturerResponseRepository,
)
from app.infrastructure.repositories.reminder_repository import SqlAlchemyReminderRepository
from app.infrastructure.repositories.timetable_slot_repository import (
    SqlAlchemyTimetableSlotRepository,
)
from app.infrastructure.scheduler.apscheduler_gateway import get_apscheduler_gateway


def build_class_session_service(session: AsyncSession) -> ClassSessionService:
    return ClassSessionService(
        SqlAlchemyClassSessionRepository(session),
        SqlAlchemyReminderRepository(session),
        SqlAlchemyAnnouncementRepository(session),
        SqlAlchemyLecturerResponseRepository(session),
        SqlAlchemyCourseRepository(session),
        SqlAlchemyLecturerRepository(session),
        SqlAlchemyCourseLecturerRepository(session),
        SqlAlchemyTimetableSlotRepository(session),
        SmtpEmailChannel(),
        get_apscheduler_gateway(),
        SqlAlchemyAuditLogWriter(session),
        session,
    )
