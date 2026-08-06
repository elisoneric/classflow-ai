import instructor
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.core.config import settings
from app.domain.models import SessionStatus

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

# We use instructor to wrap the Gemini client for structured output
# Wait, instructor supports Gemini through specific client wrappers.
# For simplicity in this script, we can just use instructor with Gemini.
import google.generativeai as genai

# Setup instructor for Gemini
client = instructor.from_gemini(
    client=genai.GenerativeModel(
        model_name="models/gemini-1.5-flash-latest",
    )
)

class AIInterpretation(BaseModel):
    status: Literal["CONFIRMED", "CANCELLED", "DELAYED", "RELOCATED", "ONLINE", "REVIEW_NEEDED"] = Field(
        description="The status of the class extracted from the lecturer's response."
    )
    new_time: Optional[str] = Field(
        description="If the class is delayed or moved to a new time, extract the new time (e.g. 15:30:00). Must be HH:MM:SS format.",
        default=None
    )
    new_venue: Optional[str] = Field(
        description="If the class is relocated, extract the new venue.",
        default=None
    )

def interpret_response(lecturer_text: str) -> AIInterpretation:
    """
    Uses Gemini to interpret a natural language response from a lecturer.
    """
    if not settings.GEMINI_API_KEY:
        # Fallback if API key is missing during dev
        return AIInterpretation(status="REVIEW_NEEDED")

    prompt = f"""
    You are an AI assistant parsing responses from university lecturers regarding their scheduled classes.
    Based on the lecturer's response, determine the new status of the class.

    Possible statuses:
    - CONFIRMED: "Yes", "Class holds", "See you there"
    - CANCELLED: "No class today", "I won't be around", "Cancel it"
    - DELAYED: "We'll start by 5pm", "I'll be 30 mins late"
    - RELOCATED: "Move to Lab 2", "Let's use the new hall"
    - ONLINE: "Hold it online", "I will send a zoom link"
    - REVIEW_NEEDED: If the response is ambiguous, unclear, or you are unsure.

    Lecturer Response: "{lecturer_text}"
    """
    
    try:
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=AIInterpretation,
        )
        return resp
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"AI parsing failed: {e}")
        return AIInterpretation(status="REVIEW_NEEDED")
