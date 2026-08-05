import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    AIInterpretedStatus,
    AnnouncementStatus,
    AuditActor,
    AuditEntityType,
    ClassMode,
    ContactMethod,
    CourseStatus,
    DayOfWeek,
    NotificationChannelType,
    ReminderStatus,
    ResolutionSource,
    SessionOutcome,
    SessionStatus,
)
from app.infrastructure.db.base import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Africa/Lagos")
    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    courses: Mapped[list["Course"]] = relationship(back_populates="semester")
    calendar_exceptions: Mapped[list["CalendarException"]] = relationship(
        back_populates="semester"
    )


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("semester_id", "code", name="uq_course_semester_code"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    semester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CourseStatus] = mapped_column(
        SAEnum(CourseStatus, name="course_status"), default=CourseStatus.ACTIVE
    )
    announcement_email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    semester: Mapped["Semester"] = relationship(back_populates="courses")
    timetable_slots: Mapped[list["TimetableSlot"]] = relationship(back_populates="course")
    lecturer_links: Mapped[list["CourseLecturer"]] = relationship(back_populates="course")
    class_sessions: Mapped[list["ClassSession"]] = relationship(back_populates="course")


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preferred_contact_method: Mapped[ContactMethod] = mapped_column(
        SAEnum(ContactMethod, name="contact_method"), default=ContactMethod.EMAIL
    )
    fallback_contact_method: Mapped[ContactMethod] = mapped_column(
        SAEnum(ContactMethod, name="contact_method"), default=ContactMethod.EMAIL
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course_links: Mapped[list["CourseLecturer"]] = relationship(back_populates="lecturer")


class CourseLecturer(Base):
    __tablename__ = "course_lecturers"

    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"), primary_key=True)
    lecturer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lecturers.id"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(default=True)

    course: Mapped["Course"] = relationship(back_populates="lecturer_links")
    lecturer: Mapped["Lecturer"] = relationship(back_populates="course_links")


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id: Mapped[uuid.UUID] = _uuid_pk()
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"), nullable=False)
    day_of_week: Mapped[DayOfWeek] = mapped_column(SAEnum(DayOfWeek, name="day_of_week"))
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[ClassMode] = mapped_column(SAEnum(ClassMode, name="class_mode"))
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False)
    response_deadline_minutes: Mapped[int] = mapped_column(default=60)
    retry_attempts: Mapped[int] = mapped_column(default=1)
    retry_interval_minutes: Mapped[int] = mapped_column(default=30)
    fallback_contact_method_override: Mapped[ContactMethod | None] = mapped_column(
        SAEnum(ContactMethod, name="contact_method"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course: Mapped["Course"] = relationship(back_populates="timetable_slots")
    class_sessions: Mapped[list["ClassSession"]] = relationship(back_populates="timetable_slot")


class ClassSession(Base):
    __tablename__ = "class_sessions"
    __table_args__ = (
        UniqueConstraint("timetable_slot_id", "session_date", name="uq_slot_session_date"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"), nullable=False)
    timetable_slot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("timetable_slots.id"), nullable=True
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    scheduled_end_time: Mapped[time] = mapped_column(Time, nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[ClassMode] = mapped_column(SAEnum(ClassMode, name="class_mode"))
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, name="session_status"), default=SessionStatus.SCHEDULED
    )
    outcome: Mapped[SessionOutcome | None] = mapped_column(
        SAEnum(SessionOutcome, name="session_outcome"), nullable=True
    )
    final_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    final_venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    final_mode: Mapped[ClassMode | None] = mapped_column(
        SAEnum(ClassMode, name="class_mode"), nullable=True
    )
    resolution_source: Mapped[ResolutionSource] = mapped_column(
        SAEnum(ResolutionSource, name="resolution_source"), default=ResolutionSource.PENDING
    )
    announced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course: Mapped["Course"] = relationship(back_populates="class_sessions")
    timetable_slot: Mapped["TimetableSlot | None"] = relationship(
        back_populates="class_sessions"
    )
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="class_session")
    responses: Mapped[list["LecturerResponse"]] = relationship(back_populates="class_session")
    announcements: Mapped[list["Announcement"]] = relationship(back_populates="class_session")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = _uuid_pk()
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("class_sessions.id"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(default=1)
    channel: Mapped[NotificationChannelType] = mapped_column(
        SAEnum(NotificationChannelType, name="notification_channel_type"),
        default=NotificationChannelType.EMAIL,
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outbound_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ReminderStatus] = mapped_column(
        SAEnum(ReminderStatus, name="reminder_status"), default=ReminderStatus.SENT
    )
    apscheduler_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    class_session: Mapped["ClassSession"] = relationship(back_populates="reminders")
    responses: Mapped[list["LecturerResponse"]] = relationship(back_populates="reminder")


class LecturerResponse(Base):
    __tablename__ = "lecturer_responses"

    id: Mapped[uuid.UUID] = _uuid_pk()
    reminder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reminders.id"), nullable=False)
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("class_sessions.id"), nullable=False
    )
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_message: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ai_status: Mapped[AIInterpretedStatus | None] = mapped_column(
        SAEnum(AIInterpretedStatus, name="ai_interpreted_status"), nullable=True
    )
    ai_new_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    ai_new_venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ai_new_mode: Mapped[ClassMode | None] = mapped_column(
        SAEnum(ClassMode, name="class_mode"), nullable=True
    )
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_raw_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    requires_review: Mapped[bool] = mapped_column(default=False)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    reminder: Mapped["Reminder"] = relationship(back_populates="responses")
    class_session: Mapped["ClassSession"] = relationship(back_populates="responses")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = _uuid_pk()
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("class_sessions.id"), nullable=False
    )
    channel: Mapped[NotificationChannelType] = mapped_column(
        SAEnum(NotificationChannelType, name="notification_channel_type"),
        default=NotificationChannelType.EMAIL,
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AnnouncementStatus | None] = mapped_column(
        SAEnum(AnnouncementStatus, name="announcement_status"), nullable=True
    )

    class_session: Mapped["ClassSession"] = relationship(back_populates="announcements")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    entity_type: Mapped[AuditEntityType] = mapped_column(
        SAEnum(AuditEntityType, name="audit_entity_type")
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[AuditActor] = mapped_column(SAEnum(AuditActor, name="audit_actor"))
    previous_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CalendarException(Base):
    __tablename__ = "calendar_exceptions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    semester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id"), nullable=True
    )

    semester: Mapped["Semester"] = relationship(back_populates="calendar_exceptions")
