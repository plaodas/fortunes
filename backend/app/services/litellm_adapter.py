from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from app import models

logger = logging.getLogger(__name__)

NUM_PREDICT = 1200
REQUEST_TIMEOUT = 900


def ollama_model_name(model: str) -> str:
    if model.startswith("ollama/"):
        return model.removeprefix("ollama/")
    return model


def ollama_chat_body(model: str, messages: list[dict[str, str]], temperature: float) -> dict[str, Any]:
    """Ollama /api/chat の本体。qwen3 だけ思考を切る。"""
    name = ollama_model_name(model)
    body: dict[str, Any] = {
        "model": name,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": NUM_PREDICT},
    }
    if "qwen3" in name:
        body["think"] = False
    return body


class LiteLlmAdapter:
    """Ollama の /api/chat を呼ぶ。クラス名は既存の呼び出しとテスト用フェイクに合わせている。"""

    def __init__(
        self,
        provider: str,
        model: str,
    ):
        self.provider: str = provider
        self.model: str = model
        self.api_base: str = os.getenv("OLLAMA_API_BASE", "http://ollama:11434")

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
        temperature: float = llm_param.get("temperature", 0.8)
        num_retries: int = llm_param.get("num_retries", 1)
        messages: list[dict[str, str]] = llm_param["messages"]

        try:
            llm_response = await self._call_llm(self.model, temperature, num_retries, messages)
            text = self._extract_text_from_response(llm_response)
            return models.LLMResponse(
                user_id=user_id,
                request_id=None,
                provider=self.provider,
                model=self.model,
                model_version=llm_response.get("model_version") or llm_response.get("model"),
                response_id=llm_response.get("id"),
                prompt_hash=None,
                response_text=text,
                usage=llm_response.get("usage"),
                raw=llm_response,
            )
        except Exception as e:
            logger.error("llm error: %s", e)
            raise

    async def _call_llm(self, model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Ollama /api/chat を呼ぶ。位置引数はテストのフェイクに合わせている。"""
        body = ollama_chat_body(model, messages, temperature)
        url = f"{self.api_base.rstrip('/')}/api/chat"
        attempts = max(1, num_retries + 1)
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    response = await client.post(url, json=body)
                    response.raise_for_status()
                    data = response.json()
                if not isinstance(data, dict):
                    raise RuntimeError("Ollama response is not an object")
                return data
            except Exception as e:
                last_error = e
        assert last_error is not None
        raise last_error

    def _extract_text_from_response(self, response_obj: dict[str, Any]) -> str:
        """Ollama の message.content、または既存フェイクの choices から本文を取る。"""
        text = _message_content(response_obj)
        if text is None or not str(text).strip():
            raise RuntimeError("LLM response content is empty")
        return str(text)


def _message_content(response_obj: dict[str, Any]) -> str | None:
    message = response_obj.get("message")
    if isinstance(message, dict) and "content" in message:
        return message.get("content")
    try:
        return response_obj["choices"][0]["message"]["content"]
    except Exception:
        return None
