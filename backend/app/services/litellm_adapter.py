from __future__ import annotations

import asyncio
import logging
import os

import litellm
from litellm import completion

logger = logging.getLogger(__name__)


async def _call_llm(model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> dict:
    """Call the provider (or return fake response). Returns raw response or string for fake.

    Calls the sync `completion` in a thread to avoid blocking the event loop.
    """
    # call blocking completion in a thread — use keyword args to avoid
    # accidental positional-argument mismatches with litellm.signature
    completion_return = await asyncio.to_thread(
        completion,
        model=model,
        messages=messages,
        temperature=temperature,
        num_retries=num_retries,
    )
    return completion_return


def _extract_text_from_response(response_obj: dict) -> str:
    """Extract textual content from various response shapes. Return text or raise."""
    # common OpenAI-like location
    try:
        return response_obj["choices"][0]["message"]["content"]
    except Exception:
        logger.error("Could not extract from response. Trying raw parsing...")

    raise RuntimeError("Could not extract text from LLM response")


async def _persist_response_to_db(response_obj: dict, provider: str, model: str, text: str) -> None:
    """Best-effort: persist LLM response to DB, but do not raise on failure.

    Uses async DB session if available.
    """
    try:
        from app import db, models

        raw_obj: dict = response_obj["raw"]

        model_version = raw_obj.get("model_version", None)
        response_id = raw_obj.get("id", None)
        usage_obj = raw_obj.get("usage", None)

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
        response = await _call_llm(model, temperature, num_retries, messages)
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
