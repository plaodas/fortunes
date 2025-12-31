import sys
import types

import pytest
from tests.utils.fake_llm_response import fake_llm_response


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
    monkeypatch.setenv("GEMINI_API_KEY", "")

    async def _fake_call_llm(model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> dict:
        return fake_llm_response(model=model, messages=messages)

    monkeypatch.setattr("app.services.litellm_adapter._call_llm", _fake_call_llm)

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
