from __future__ import annotations

import logging
import os

import litellm
from litellm import completion

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


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


def _call_llm(provider: str, model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> object | str:
    """Call the provider (or return fake response). Returns raw response or string for fake."""
    if _is_debug_fake():
        return _fake_response(model=model, messages=messages)

    return completion(
        model=model,
        temperature=temperature,
        num_retries=num_retries,
        messages=messages,
    )


def _extract_text_from_response(response_obj: object | str) -> str:
    """Extract textual content from various response shapes. Return text or raise."""
    # if fake path returns a string already
    if isinstance(response_obj, str):
        return response_obj

    # common OpenAI-like location
    try:
        return response_obj.choices[0].message.content
    except Exception:
        logger.debug("Could not extract from response. Trying raw parsing...")

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


def _persist_response_to_db(response_obj: object | str, provider: str, model: str, text: str) -> None:
    """Best-effort: persist LLM response to DB, but do not raise on failure."""
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

        with db.SessionLocal() as session:
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
    except Exception as e:
        logger.warning("Could not persist LLM response: %s", e)


def _generate(**llm_param) -> str:
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
        response = _call_llm(provider, model, temperature, num_retries, messages)
        text = _extract_text_from_response(response)
        _persist_response_to_db(response, provider, model, text)
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


def make_analysis_detail(system_prompt: str, user_prompt: str) -> dict:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    return _generate(
        provider="vertex_ai",
        # model="gemini/gemini-2.5-pro",
        model="gemini/gemini-2.5-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )


def make_analysis_summary(system_prompt: str, user_prompt: str) -> dict:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    return _generate(
        provider="vertex_ai",
        model="gemini/gemini-2.5-flash-lite",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
