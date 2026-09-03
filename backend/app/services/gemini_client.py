import asyncio
import os
from typing import Type, TypeVar, Optional, Any, List, Union
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError, APIError
from ..config import GEMINI_API_KEY, GEMINI_API_KEYS, GEMINI_MODEL

T = TypeVar("T", bound=BaseModel)

# ── Key pool: built entirely from environment variables, never hardcoded ──
_KEY_POOL: List[str] = [k.strip() for k in GEMINI_API_KEYS.split(",") if k.strip()]
if GEMINI_API_KEY and GEMINI_API_KEY not in _KEY_POOL:
    _KEY_POOL.insert(0, GEMINI_API_KEY)

if not _KEY_POOL:
    print("WARNING: No Gemini API keys configured. Set GEMINI_API_KEY or GEMINI_API_KEYS env vars.")

_clients: List[genai.Client] = []
_key_index = 0


def _init_clients():
    """Lazily initialize client pool from key pool."""
    global _clients
    if _clients:
        return
    for k in _KEY_POOL:
        try:
            _clients.append(genai.Client(api_key=k))
        except Exception as e:
            print(f"Warning: Failed to init Gemini client for key ending ...{k[-6:]}: {e}")


def _rotate_client() -> Optional[genai.Client]:
    """Return the next client in round-robin order."""
    global _key_index
    _init_clients()
    if not _clients:
        return None
    client = _clients[_key_index % len(_clients)]
    _key_index += 1
    return client


class GeminiQuotaExhaustedError(Exception):
    """Raised when all keys in the pool have been exhausted (429/RESOURCE_EXHAUSTED)."""
    pass


async def generate_structured(
    prompt: Union[str, List[Any]],
    schema: Type[T],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_retries: int = 6
) -> T:
    """
    Generate structured output using google-genai with multi-key pool rotation.
    On 429/RESOURCE_EXHAUSTED: rotates to next key immediately (no sleep),
    only backs off once ALL keys have been tried in the current round.
    """
    target_model = model or GEMINI_MODEL or "gemini-3.5-flash"

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
        system_instruction=system_instruction
    )

    loop = asyncio.get_running_loop()
    pool_size = max(len(_KEY_POOL), 1)
    consecutive_429s = 0

    for attempt in range(max_retries):
        client = _rotate_client()
        if not client:
            raise GeminiQuotaExhaustedError("No valid Gemini API keys configured.")

        try:
            def _call():
                return client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config
                )

            response = await loop.run_in_executor(None, _call)
            consecutive_429s = 0  # Reset on success

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
                consecutive_429s += 1
                key_suffix = f"...{_KEY_POOL[(_key_index - 1) % pool_size][-6:]}" if _KEY_POOL else "?"
                print(f"[Gemini 429] Key {key_suffix} exhausted, rotating (attempt {attempt + 1}/{max_retries}, consecutive={consecutive_429s})")
                # Only sleep after we've tried every key in the pool
                if consecutive_429s >= pool_size:
                    consecutive_429s = 0
                    print(f"[Gemini] All {pool_size} keys exhausted this round. Backing off 10s...")
                    await asyncio.sleep(10.0)
                # Otherwise rotate immediately, no sleep
            else:
                if attempt == max_retries - 1:
                    raise api_err
                await asyncio.sleep(2.0)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2.0)

    raise GeminiQuotaExhaustedError(
        f"All {pool_size} Gemini API keys exhausted after {max_retries} attempts. "
        "Quota resets at midnight Pacific Time."
    )


async def generate_text(
    prompt: Union[str, List[Any]],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_retries: int = 6
) -> str:
    """
    Generate plain text with multi-key pool rotation and immediate key-switch on 429.
    """
    target_model = model or GEMINI_MODEL or "gemini-3.5-flash"

    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction
    )

    loop = asyncio.get_running_loop()
    pool_size = max(len(_KEY_POOL), 1)
    consecutive_429s = 0

    for attempt in range(max_retries):
        client = _rotate_client()
        if not client:
            raise GeminiQuotaExhaustedError("No valid Gemini API keys configured.")

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
                consecutive_429s += 1
                key_suffix = f"...{_KEY_POOL[(_key_index - 1) % pool_size][-6:]}" if _KEY_POOL else "?"
                print(f"[Gemini 429] Key {key_suffix} exhausted, rotating (attempt {attempt + 1}/{max_retries})")
                if consecutive_429s >= pool_size:
                    consecutive_429s = 0
                    print(f"[Gemini] All {pool_size} keys exhausted this round. Backing off 10s...")
                    await asyncio.sleep(10.0)
            else:
                if attempt == max_retries - 1:
                    raise api_err
                await asyncio.sleep(2.0)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2.0)

    return ""
