import sys
import types

import pytest


@pytest.fixture(autouse=True)
def ci_test_environment(monkeypatch):
    """Autouse fixture for CI/tests that stubs external dependencies and
    configures environment for deterministic behavior.

    - Provide a minimal `litellm` module so imports succeed and return
      predictable fake responses.
    - Provide a minimal `jinja2.Environment` stub so templates don't require
      real Jinja2 rendering in tests.
    - Set environment variables to ensure adapter uses fake responses.
    """
    # ensure tests use fake LLM responses
    monkeypatch.setenv("DEBUG_LITELLM_FAKE_RESP", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    # -- litellm stub
    litellm_mod = types.ModuleType("litellm")

    class AuthenticationError(Exception):
        pass

    class RateLimitError(Exception):
        pass

    class APIError(Exception):
        pass

    def completion(*args, **kwargs):
        # Provide a response with both simple `.choices[0].message.content`
        # and a `raw` dict with nested candidates to exercise extraction logic.
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="[FAKE RESP]"))],
            raw={
                "id": "fake",
                "choices": [{"message": {"parts": [{"text": "[FAKE RESP]"}]}}],
                "usage": {},
            },
        )

    def _turn_on_debug():
        return None

    litellm_mod.completion = completion
    litellm_mod.AuthenticationError = AuthenticationError
    litellm_mod.RateLimitError = RateLimitError
    litellm_mod.APIError = APIError
    litellm_mod._turn_on_debug = _turn_on_debug

    monkeypatch.setitem(sys.modules, "litellm", litellm_mod)

    # -- jinja2 stub (safe no-op rendering)
    jinja_mod = types.ModuleType("jinja2")

    class Environment:
        def __init__(self, *args, **kwargs):
            pass

        def from_string(self, template: str):
            def render(**context):
                return template

            return types.SimpleNamespace(render=render)

    jinja_mod.Environment = Environment
    monkeypatch.setitem(sys.modules, "jinja2", jinja_mod)

    yield
