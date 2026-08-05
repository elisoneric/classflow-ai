from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.domain.enums import AIInterpretedStatus, ClassMode
from app.domain.value_objects import Interpretation, SessionContext

PROMPT_VERSION = "v1"

_TOOL_SCHEMA = {
    "name": "record_interpretation",
    "description": (
        "Record the structured interpretation of a lecturer's reply about "
        "whether a scheduled class is holding."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["CONFIRMED", "CANCELLED", "DELAYED", "RELOCATED", "ONLINE", "UNCLEAR"],
            },
            "new_time": {
                "type": ["string", "null"],
                "description": "HH:MM 24-hour time — only when status is DELAYED",
            },
            "new_venue": {
                "type": ["string", "null"],
                "description": "only when status is RELOCATED",
            },
            "new_mode": {
                "type": ["string", "null"],
                "enum": ["IN_PERSON", "ONLINE", "HYBRID", None],
                "description": "only when status is ONLINE",
            },
            "confidence": {
                "type": "number",
                "description": "0.0-1.0, self-reported per the rubric in the system prompt",
            },
            "reasoning": {"type": "string", "description": "one sentence"},
        },
        "required": ["status", "confidence", "reasoning"],
    },
}

_SYSTEM_PROMPT = """You interpret a university lecturer's short, informal reply about whether a \
scheduled class is holding today. You do not chat or respond conversationally — you only classify.

Classify into exactly one status:
- CONFIRMED: class is holding as scheduled
- CANCELLED: class is not holding today
- DELAYED: class is holding but starting later than scheduled (extract new_time)
- RELOCATED: class is holding but at a different venue (extract new_venue)
- ONLINE: class is holding but moved online (set new_mode=ONLINE)
- UNCLEAR: the reply doesn't clearly address whether this class is holding — off-topic, \
contradictory, multi-intent, or ambiguous

Confidence rubric (self-reported, 0.0-1.0):
- High (0.85-1.0): a single, explicit, unambiguous statement about this class's status
- Medium (0.5-0.84): implied or partial — status is inferable but not stated outright
- Low (<0.5): off-topic, contradictory, multi-intent, or you are genuinely guessing

Always call record_interpretation with your answer. Never leave a field you're unsure about — \
use UNCLEAR with low confidence instead of guessing at a specific outcome."""


class AnthropicInterpreter:
    """MessageInterpreter adapter over Claude. See PROJECT.md §11 (ADR-4)."""

    def __init__(self):
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def interpret(self, raw_message: str, context: SessionContext) -> Interpretation:
        user_prompt = (
            f"Course: {context.course_code} — {context.course_title}\n"
            f"Lecturer: {context.lecturer_name}\n"
            f"Scheduled: {context.session_date} at {context.scheduled_start_time}, "
            f"venue {context.scheduled_venue}, mode {context.scheduled_mode.value}\n\n"
            f"Lecturer's reply:\n{raw_message}"
        )

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "record_interpretation"},
            messages=[{"role": "user", "content": user_prompt}],
        )

        tool_use = next(block for block in response.content if block.type == "tool_use")
        data = tool_use.input

        new_mode = ClassMode(data["new_mode"]) if data.get("new_mode") else None

        return Interpretation(
            status=AIInterpretedStatus(data["status"]),
            confidence=float(data["confidence"]),
            reasoning=data.get("reasoning", ""),
            new_time=data.get("new_time"),
            new_venue=data.get("new_venue"),
            new_mode=new_mode,
            model_name=self._model,
            prompt_version=PROMPT_VERSION,
            raw_output=data,
        )
