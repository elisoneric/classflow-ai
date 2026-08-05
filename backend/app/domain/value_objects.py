from dataclasses import dataclass

from app.domain.enums import AIInterpretedStatus, ClassMode


@dataclass(frozen=True, slots=True)
class SessionContext:
    """Context handed to the AI interpreter — everything it needs to judge a reply."""

    course_code: str
    course_title: str
    lecturer_name: str
    session_date: str
    scheduled_start_time: str
    scheduled_venue: str
    scheduled_mode: ClassMode


@dataclass(frozen=True, slots=True)
class Interpretation:
    """Structured output of MessageInterpreter.interpret(). Mirrors PROJECT.md §11."""

    status: AIInterpretedStatus
    confidence: float
    reasoning: str
    new_time: str | None = None
    new_venue: str | None = None
    new_mode: ClassMode | None = None
    model_name: str = ""
    prompt_version: str = ""
    raw_output: dict | None = None


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    success: bool
    provider_message_id: str | None = None
    error: str | None = None
