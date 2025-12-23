# TODO: Tracking costs per provider/model

from __future__ import annotations

import logging
import os

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


def _generate(**llm_param) -> str:
    model: str = llm_param["model"]
    temperature: float = llm_param.get("temperature", 0.8)  # 創造性を少し高めるために0.8程度に設定
    num_retries: int = llm_param.get("num_retries", 3)  # エラーが出たら3回まで自動で再試行する
    messages: list[dict[str, str]] = llm_param["messages"]

    # If tests or runtime requested a fake response, check at call-time
    if _is_debug_fake():
        return _fake_response(model=model, messages=messages)

    try:
        response = completion(
            model=model,
            temperature=temperature,
            num_retries=num_retries,
            messages=messages,
        )
        return response.choices[0].message.content
    except litellm.AuthenticationError as e:
        # Thrown when the API key is invalid
        logger.error(f"llm AuthenticationError: {str(e)}")
    except litellm.RateLimitError as e:
        # Thrown when you've exceeded your rate limit
        logger.error(f"llm RateLimitError: {str(e)}")
    except litellm.APIError as e:
        # Thrown for general API errors
        logger.error(f"llm APIError: {str(e)}")
    except Exception as e:
        logger.error(f"llm error: {str(e)}")
        raise e


def make_analysis_detail(system_prompt: str, user_prompt: str) -> dict:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    return _generate(
        model="gemini/gemini-2.5-pro",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )


def make_analysis_summary(system_prompt: str, user_prompt: str) -> dict:
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    return _generate(
        model="gemini/gemini-1.5-pro",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
