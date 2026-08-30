import asyncio
import time
import os
from typing import Type, TypeVar, Optional, Any, List, Union
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError, APIError
from ..config import GEMINI_API_KEY, GEMINI_MODEL

T = TypeVar("T", bound=BaseModel)

# Key pool supporting primary + backup keys for maximum throughput
_KEY_POOL = [
    "YOUR_GEMINI_API_KEY",
    "YOUR_GEMINI_BACKUP_KEY"
]
if GEMINI_API_KEY and GEMINI_API_KEY not in _KEY_POOL:
    _KEY_POOL.insert(0, GEMINI_API_KEY)

_clients: List[genai.Client] = []
_key_index = 0


def _get_client() -> Optional[genai.Client]:
    global _clients, _key_index
    if not _clients:
        for k in _KEY_POOL:
            try:
                _clients.append(genai.Client(api_key=k))
            except Exception as e:
                print(f"Warning: Failed to init client for key: {e}")
    if not _clients:
        return None
    client = _clients[_key_index % len(_clients)]
    _key_index += 1
    return client


async def generate_structured(
    prompt: Union[str, List[Any]],
    schema: Type[T],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_retries: int = 6
) -> T:
    """
    Generate structured output using google-genai with multi-key pool and 429/503 automatic backoff.
    """
    target_model = model or GEMINI_MODEL or "gemini-3.5-flash"

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
        system_instruction=system_instruction
    )

    loop = asyncio.get_running_loop()

    for attempt in range(max_retries):
        client = _get_client()
        if not client:
            raise ValueError("No valid Gemini client available.")

        try:
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

            if hasattr(response, "text") and response.text:
                return schema.model_validate_json(response.text)

            raise ValueError("Empty response from Gemini model.")
        except (ClientError, ServerError, APIError) as api_err:
            err_str = str(api_err)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                wait_time = 6.0 * (attempt + 1)
                print(f"[Gemini Rate/Demand Backoff] Switching key pool & waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            else:
                if attempt == max_retries - 1:
                    raise api_err
                await asyncio.sleep(3.0)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(3.0)

    raise ValueError("Max retries exceeded for Gemini generate_structured.")


async def generate_text(
    prompt: Union[str, List[Any]],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_retries: int = 6
) -> str:
    """
    Generate plain text with multi-key pool rotation and backoff.
    """
    target_model = model or GEMINI_MODEL or "gemini-3.5-flash"

    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction
    )

    loop = asyncio.get_running_loop()

    for attempt in range(max_retries):
        client = _get_client()
        if not client:
            raise ValueError("No valid Gemini client available.")

        try:
            def _call():
                return client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config
                )

            response = await loop.run_in_executor(None, _call)
            return response.text or ""
        except (ClientError, ServerError, APIError) as api_err:
            err_str = str(api_err)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                wait_time = 6.0 * (attempt + 1)
                print(f"[Gemini Rate/Demand Backoff] Switching key pool & waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            else:
                if attempt == max_retries - 1:
                    raise api_err
                await asyncio.sleep(3.0)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(3.0)

    return ""
