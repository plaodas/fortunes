from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, cast

import litellm
from litellm import completion

logger = logging.getLogger(__name__)


def _is_debug_fake() -> bool:
    """Return True when runtime env requests a fake response (checked at call time).

    This allows tests to set `os.environ['DEBUG_LITELLM_FAKE_RESP'] = '1'`
    dynamically without needing to reload the module.
    """
    return os.getenv("DEBUG_LITELLM_FAKE_RESP", "0") in ("1", "true", "True")


def _fake_response(model: str, messages: list[dict[str, str]]) -> str:
    message = f"system_prompt_preview={messages[0]['content'][:80]} user_prompt_preview={messages[1]['content'][:80]}"
    logger.info("DEBUG mode: returning fake response")
    return f"[FAKE RESP] model={model} {message}"


async def _call_llm(provider: str, model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> Any | str:
    """Call the provider (or return fake response). Returns raw response or string for fake.

    Calls the sync `completion` in a thread to avoid blocking the event loop.
    """
    if _is_debug_fake():
        return _fake_response(model=model, messages=messages)

    # call blocking completion in a thread — use keyword args to avoid
    # accidental positional-argument mismatches with litellm.signature
    return await asyncio.to_thread(
        completion,
        model=model,
        messages=messages,
        temperature=temperature,
        num_retries=num_retries,
    )


def _extract_text_from_response(response_obj: Any | str) -> str:
    """Extract textual content from various response shapes. Return text or raise."""
    # if fake path returns a string already
    if isinstance(response_obj, str):
        return response_obj

    # common OpenAI-like location
    try:
        return response_obj.choices[0].message.content
    except Exception:
        logger.warning("Could not extract from response. Trying raw parsing...")

    # try to parse raw/dict forms
    raw = None
    try:
        raw = getattr(response_obj, "raw", None) or (response_obj.to_dict() if hasattr(response_obj, "to_dict") else None)
    except Exception:
        raw = None

    if isinstance(raw, dict):
        candidates = raw.get("candidates") or raw.get("choices")
        if candidates and isinstance(candidates, list) and len(candidates) > 0:
            part = candidates[0].get("content") or candidates[0].get("message")
            if isinstance(part, dict):
                parts = part.get("parts")
                if parts and isinstance(parts, list):
                    maybe = parts[0].get("text")
                    if maybe:
                        return maybe

    raise RuntimeError("Could not extract text from LLM response")


async def _persist_response_to_db(response_obj: Any | str, provider: str, model: str, text: str) -> None:
    """Best-effort: persist LLM response to DB, but do not raise on failure.

    Uses async DB session if available.
    """
    try:
        from app import db, models

        raw_obj = None
        try:
            raw_obj = getattr(response_obj, "raw", None) or (response_obj.to_dict() if hasattr(response_obj, "to_dict") else None)
        except Exception:
            raw_obj = None

        model_version = None
        response_id = None
        usage_obj = None
        if isinstance(raw_obj, dict):
            model_version = raw_obj.get("modelVersion") or raw_obj.get("model_version")
            response_id = raw_obj.get("responseId") or raw_obj.get("id")
            usage_obj = raw_obj.get("usageMetadata") or raw_obj.get("usage")

        # use async session if available
        try:
            async with db.SessionLocal() as session:
                rec = models.LLMResponse(
                    request_id=None,
                    provider=provider,
                    model=model,
                    model_version=model_version,
                    response_id=response_id,
                    prompt_hash=None,
                    response_text=text,
                    usage=usage_obj,
                    raw=raw_obj,
                )
                session.add(rec)
                await session.commit()
        except Exception:
            # fallback to sync path if project still exposes sync SessionLocal
            try:
                with cast(Any, db.SessionLocal)() as session:
                    rec = models.LLMResponse(
                        request_id=None,
                        provider=provider,
                        model=model,
                        model_version=model_version,
                        response_id=response_id,
                        prompt_hash=None,
                        response_text=text,
                        usage=usage_obj,
                        raw=raw_obj,
                    )
                    session.add(rec)
                    session.commit()
            except Exception:
                pass
    except Exception as e:
        logger.warning("Could not persist LLM response: %s", e)


async def _generate(**llm_param) -> str:
    """Generic LLM call wrapper for litellm.

    args:
        llm_param: dict with keys:
        - provider: str
        - model: str
        - temperature: float (optional)
        - num_retries: int (optional)
        - messages: list[dict[str, str]]
    """
    provider: str = llm_param["provider"]
    model: str = llm_param["model"]
    temperature: float = llm_param.get("temperature", 0.8)
    num_retries: int = llm_param.get("num_retries", 3)
    messages: list[dict[str, str]] = llm_param["messages"]

    try:
        response = await _call_llm(provider, model, temperature, num_retries, messages)
        text = _extract_text_from_response(response)
        # persist in background (don't await to keep latency low)
        asyncio.create_task(_persist_response_to_db(response, provider, model, text))

        return text

    except litellm.AuthenticationError as e:
        logger.error("llm AuthenticationError: %s", e)
        raise
    except litellm.RateLimitError as e:
        logger.error("llm RateLimitError: %s", e)
        raise
    except litellm.APIError as e:
        logger.error("llm APIError: %s", e)
        raise
    except Exception as e:
        logger.error("llm error: %s", e)
        raise


async def make_analysis_detail(system_prompt: str, user_prompt: str) -> str:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    return await _generate(
        provider="vertex_ai",
        # model="gemini/gemini-2.5-pro",
        model="gemini/gemini-2.5-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )


async def make_analysis_summary(system_prompt: str, user_prompt: str) -> str:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    return await _generate(
        provider="vertex_ai",
        model="gemini/gemini-2.5-flash-lite",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
