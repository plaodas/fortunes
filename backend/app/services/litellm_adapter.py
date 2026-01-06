from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import litellm
from app import models
from litellm import completion

logger = logging.getLogger(__name__)


class LiteLlmAdapter:
    """Adapter for litellm LLM calls."""

    def __init__(
        self,
        provider: str,
        model: str,
    ):
        self.provider: str = provider
        self.model: str = model
        os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

    async def make_analysis(self, user_id: int, system_prompt: str, user_prompt: str) -> models.LLMResponse:
        return await self._generate(
            user_id=user_id,
            provider=self.provider,
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    async def _generate(self, user_id: int, **llm_param) -> models.LLMResponse:
        """Generic LLM call wrapper for litellm.

        args:
            user_id: int
            llm_param: dict with keys:
            - provider: str
            - model: str
            - temperature: float (optional)
            - num_retries: int (optional)
            - messages: list[dict[str, str]]
        """
        temperature: float = llm_param.get("temperature", 0.8)
        num_retries: int = llm_param.get("num_retries", 3)
        messages: list[dict[str, str]] = llm_param["messages"]

        try:
            llm_response = await self._call_llm(self.model, temperature, num_retries, messages)
            text = self._extract_text_from_response(llm_response)
            model_version = llm_response.get("model_version", None)
            response_id = llm_response.get("id", None)
            usage_obj = llm_response.get("usage", None)
            return models.LLMResponse(
                user_id=user_id,
                request_id=None,
                provider=self.provider,
                model=self.model,
                model_version=model_version,
                response_id=response_id,
                prompt_hash=None,
                response_text=text,
                usage=usage_obj,
                raw=llm_response,
            )

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

    async def _call_llm(self, model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> dict[str, Any]:
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

    def _extract_text_from_response(self, response_obj: dict[str, Any]) -> str:
        """Extract textual content from various response shapes. Return text or raise."""
        # common OpenAI-like location
        try:
            return response_obj["choices"][0]["message"]["content"]
        except Exception:
            logger.error("Could not extract from response. Trying raw parsing...")

        raise RuntimeError("Could not extract text from LLM response")
