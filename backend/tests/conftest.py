import sys
import types
from typing import Any, AsyncGenerator

import pytest

# test HTTP client
from app.main import app
from httpx import ASGITransport, AsyncClient
from tests.utils.fake_llm_response import fake_llm_response

# Ensure pytest-asyncio plugin is loaded so async fixtures/tests are handled
pytest_plugins = ("pytest_asyncio",)


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

    async def _fake_call_llm(ctx: Any, model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> dict[str, Any]:
        return fake_llm_response(model=model, messages=messages)

    monkeypatch.setattr("app.services.litellm_adapter.LiteLlmAdapter._call_llm", _fake_call_llm)

    # Avoid using real bcrypt hashing in tests (some bcrypt builds raise on long detection strings).
    # Provide a simple deterministic hash function for tests. Patch both the auth module
    # and the already-imported reference in user_service so tests that imported the
    # symbol at module import time also use the stub.
    def stub_hash(pw: str) -> str:
        return f"testhash:{pw[:60]}"

    monkeypatch.setattr("app.auth.get_password_hash", stub_hash)
    monkeypatch.setattr("app.services.user_service.get_password_hash", stub_hash, raising=False)

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


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Ensure DB schema exists for tests by running the simple migration runner.

    This uses `backend/manage_migrate.py` which reads `DATABASE_URL` to
    target the test database. Running migrations here avoids "relation
    \"user\" does not exist" errors in tests that access the DB.
    """
    try:
        from backend import manage_migrate

        manage_migrate.run_migrations(["init.sql", "02_create_users.sql"])
    except Exception:
        # Don't fail import-time if migrations cannot be applied; let tests
        # surface DB errors so CI logs show the underlying cause.
        pass


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an `httpx.AsyncClient` bound to the FastAPI app for tests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def logged_in_client(async_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Log in via the real auth endpoint and return a client with cookies set."""
    # use demo/demo as in tests that exercise auth flow
    resp = await async_client.post("/api/v1/auth/login", data={"username": "demo", "password": "demo"})
    assert resp.status_code == 200
    # Set CSRF header for subsequent unsafe requests (double-submit)
    csrf = async_client.cookies.get("csrf_token")
    if csrf:
        async_client.headers.update({"x-csrf-token": csrf})
    yield async_client
