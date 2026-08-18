from typing import Type, TypeVar, Optional, Any, List, Union
from pydantic import BaseModel
from google import genai
from google.genai import types
from ..config import GEMINI_API_KEY, GEMINI_MODEL

T = TypeVar("T", bound=BaseModel)

_client: Optional[genai.Client] = None


def get_gemini_client() -> Optional[genai.Client]:
    global _client
    if _client is None and GEMINI_API_KEY:
        try:
            _client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini client: {e}")
    return _client


async def generate_structured(
    prompt: Union[str, List[Any]],
    schema: Type[T],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2
) -> T:
    """
    Generate structured output using google-genai 2.18.1.
    Supports Pydantic schema validation.
    """
    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY is not configured.")

    target_model = model or GEMINI_MODEL

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
        system_instruction=system_instruction
    )

    # genai.Client models.generate_content is synchronous; run via asyncio executor or directly
    import asyncio
    loop = asyncio.get_running_loop()

    def _call():
        return client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config
        )

    response = await loop.run_in_executor(None, _call)

    if hasattr(response, "parsed") and response.parsed is not None:
        if isinstance(response.parsed, schema):
            return response.parsed
        if isinstance(response.parsed, dict):
            return schema(**response.parsed)

    # Fallback to parsing text
    if hasattr(response, "text") and response.text:
        return schema.model_validate_json(response.text)

    raise ValueError("Empty or invalid response from Gemini model.")


async def generate_text(
    prompt: Union[str, List[Any]],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4
) -> str:
    """
    Generate plain text with Gemini.
    """
    client = get_gemini_client()
    if not client:
        raise ValueError("GEMINI_API_KEY is not configured.")

    target_model = model or GEMINI_MODEL

    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction
    )

    import asyncio
    loop = asyncio.get_running_loop()

    def _call():
        return client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config
        )

    response = await loop.run_in_executor(None, _call)
    return response.text or ""
