from google.genai import types

from app.infrastructure.ai.gemini_interpreter import _RESPONSE_SCHEMA


def test_response_schema_validates_against_gemini_schema_type():
    """Guards against the schema drifting out of sync with the SDK's supported
    OpenAPI-3.0 subset (e.g. accidentally using JSON Schema's type-union
    nullability instead of Gemini's `nullable: true`).
    """
    schema = types.Schema.model_validate(_RESPONSE_SCHEMA)
    assert schema.type == types.Type.OBJECT
    assert schema.required == ["status", "confidence", "reasoning"]
    assert schema.properties["new_time"].nullable is True
