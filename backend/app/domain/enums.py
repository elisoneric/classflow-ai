from enum import StrEnum


class CourseStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class ContactMethod(StrEnum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"  # not yet implemented — see ADR-1 in PROJECT.md


class ClassMode(StrEnum):
    IN_PERSON = "IN_PERSON"
    ONLINE = "ONLINE"
    HYBRID = "HYBRID"


class DayOfWeek(StrEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class SessionStatus(StrEnum):
    """Pipeline stage — where the session is in the workflow. See PROJECT.md §7 state machine."""

    SCHEDULED = "SCHEDULED"
    REMINDER_SENT = "REMINDER_SENT"
    PENDING_REVIEW = "PENDING_REVIEW"
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    ANNOUNCED = "ANNOUNCED"


class SessionOutcome(StrEnum):
    """The actual class result — distinct from SessionStatus. See ADR-8."""

    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"
    RELOCATED = "RELOCATED"
    ONLINE = "ONLINE"
    UNRESOLVED = "UNRESOLVED"


class AIInterpretedStatus(StrEnum):
    """Raw classification the AI can return — see PROJECT.md §11. UNCLEAR always routes to review."""

    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"
    RELOCATED = "RELOCATED"
    ONLINE = "ONLINE"
    UNCLEAR = "UNCLEAR"


class ResolutionSource(StrEnum):
    PENDING = "PENDING"
    LECTURER_RESPONSE = "LECTURER_RESPONSE"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    NO_RESPONSE_FALLBACK = "NO_RESPONSE_FALLBACK"


class ReminderStatus(StrEnum):
    SENT = "SENT"
    RESPONDED = "RESPONDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class NotificationChannelType(StrEnum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"  # not yet implemented — see ADR-1 in PROJECT.md


class AnnouncementStatus(StrEnum):
    SENT = "SENT"
    FAILED = "FAILED"


class AuditActor(StrEnum):
    SYSTEM = "SYSTEM"
    LECTURER = "LECTURER"
    COURSE_REP = "COURSE_REP"


class AuditEntityType(StrEnum):
    SEMESTER = "SEMESTER"
    COURSE = "COURSE"
    LECTURER = "LECTURER"
    TIMETABLE_SLOT = "TIMETABLE_SLOT"
    CLASS_SESSION = "CLASS_SESSION"
    REMINDER = "REMINDER"
    ANNOUNCEMENT = "ANNOUNCEMENT"
