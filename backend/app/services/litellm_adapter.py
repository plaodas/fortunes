"""Simple adapter showing how to switch LLM providers per request.

This is a lightweight example. It attempts to call provider SDKs if installed;
otherwise it raises a helpful error. For local development you can enable
`DEBUG_LITELLM_FAKE_RESP=1` in the environment to get a canned response.

Supported providers: "openai", "gemini", "deepseek" (placeholders).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEBUG_FAKE = os.getenv("DEBUG_LITELLM_FAKE_RESP", "0") in ("1", "true", "True")


def something(client):
    pass


def _fake_response(model: str, prompt: str) -> str:
    return f"[FAKE RESP] model={model} prompt_preview={prompt[:80]}"


def generate(provider: str, model: str, prompt: str, **kwargs) -> str:
    """Generate text using selected provider.

    Returns the generated text (string). Raises RuntimeError with a helpful
    message when required SDKs or keys are missing.
    """
    if DEBUG_FAKE:
        logger.info("DEBUG mode: returning fake response")
        return _fake_response(model, prompt)

    provider = (provider or "").lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        try:
            import openai

            openai.api_key = api_key
            # simple ChatCompletion call; adapt as needed
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
            )
            return resp.choices[0].message.content
        except ImportError as e:
            raise RuntimeError("openai package not installed; pip install openai") from e

    if provider in ("gemini", "google"):
        # Placeholder for calling Google Vertex AI / Gemini. Users should
        # install google-cloud-aiplatform and then call the appropriate client.
        try:
            from google.cloud import aiplatform  # type: ignore

            # The exact call varies by SDK version and model type; here's a sketch
            client = aiplatform.gapic.PredictionServiceClient()
            # TODO: fill project/location/endpoint and call predict() accordingly
            something(client)

            raise NotImplementedError("Gemini/Vertex AI call not implemented in sample adapter")
        except ImportError as e:
            raise RuntimeError("google-cloud-aiplatform not installed; see docs to install and configure") from e

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
        try:
            import requests

            # NOTE: replace URL with DeepSeek's actual API endpoint and payload
            url = "https://api.deepseek.example/v1/generate"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": model, "prompt": prompt}
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            # adjust according to real response shape
            return data.get("text") or data.get("output") or str(data)
        except ImportError as e:
            raise RuntimeError("requests package not available; pip install requests") from e

    raise RuntimeError(f"Unsupported provider: {provider}")
