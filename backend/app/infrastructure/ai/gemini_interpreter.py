import json

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.domain.enums import AIInterpretedStatus, ClassMode
from app.domain.value_objects import Interpretation, SessionContext

PROMPT_VERSION = "v1"

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["CONFIRMED", "CANCELLED", "DELAYED", "RELOCATED", "ONLINE", "UNCLEAR"],
        },
        "new_time": {
            "type": "string",
            "nullable": True,
            "description": "HH:MM 24-hour time — only when status is DELAYED",
        },
        "new_venue": {
            "type": "string",
            "nullable": True,
            "description": "only when status is RELOCATED",
        },
        "new_mode": {
            "type": "string",
            "enum": ["IN_PERSON", "ONLINE", "HYBRID"],
            "nullable": True,
            "description": "only when status is ONLINE",
        },
        "confidence": {
            "type": "number",
            "description": "0.0-1.0, self-reported per the rubric in the system prompt",
        },
        "reasoning": {"type": "string", "description": "one sentence"},
    },
    "required": ["status", "confidence", "reasoning"],
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

Respond with a single JSON object matching the given schema. Never leave a field you're unsure \
about — use UNCLEAR with low confidence instead of guessing at a specific outcome."""


class GeminiInterpreter:
    """MessageInterpreter adapter over Gemini. See PROJECT.md §11 (ADR-4).

    Uses response_schema structured output (not function calling) to force
    JSON-shaped output — Gemini's `Schema` type is an OpenAPI-3.0 subset, so
    optional fields use `nullable: true` rather than a JSON Schema type union.
    """

    def __init__(self):
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def interpret(self, raw_message: str, context: SessionContext) -> Interpretation:
        user_prompt = (
            f"Course: {context.course_code} — {context.course_title}\n"
            f"Lecturer: {context.lecturer_name}\n"
            f"Scheduled: {context.session_date} at {context.scheduled_start_time}, "
            f"venue {context.scheduled_venue}, mode {context.scheduled_mode.value}\n\n"
            f"Lecturer's reply:\n{raw_message}"
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=_RESPONSE_SCHEMA,
            ),
        )

        data = json.loads(response.text)
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
