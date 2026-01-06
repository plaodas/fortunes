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


def _patch_litellm(monkeypatch):
    """Patch LiteLlmAdapter to return deterministic fake responses."""

    async def _fake_call_llm(ctx: Any, model: str, temperature: float, num_retries: int, messages: list[dict[str, str]]) -> dict[str, Any]:
        return fake_llm_response(model=model, messages=messages)

    monkeypatch.setattr("app.services.litellm_adapter.LiteLlmAdapter._call_llm", _fake_call_llm)


def _patch_hashes(monkeypatch):
    """Stub password hashing and verification for tests."""

    def stub_hash(pw: str) -> str:
        return f"testhash:{pw[:60]}"

    def stub_verify(plain: str, hashed: str) -> bool:
        if not isinstance(hashed, str):
            return False
        if hashed.startswith("testhash:"):
            return hashed == f"testhash:{plain[:60]}"
        try:
            from app.auth import verify_password as real_verify

            return real_verify(plain, hashed)
        except Exception:
            return False

    monkeypatch.setattr("app.auth.get_password_hash", stub_hash)
    monkeypatch.setattr("app.services.user_service.get_password_hash", stub_hash, raising=False)
    monkeypatch.setattr("app.auth.verify_password", stub_verify)


def _patch_jinja(monkeypatch):
    """Provide a minimal jinja2.Environment stub."""
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


def _ensure_demo_user():
    """Ensure a 'demo' user exists by running a short async seeding routine."""
    try:
        import asyncio

        from app.db import SessionLocal
        from app.services.user_service import create_user, get_user_by_username

        async def _seed():
            async with SessionLocal() as session:
                existing = await get_user_by_username(session, "demo")
                if not existing:
                    try:
                        await create_user(session, username="demo", password="demo", email="demo@example.com", display_name="Demo User")
                    except Exception:
                        pass

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_seed())
        finally:
            loop.close()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def ci_test_environment(monkeypatch):
    """Autouse fixture that composes smaller test-environment patches."""
    # ensure tests use fake LLM responses
    monkeypatch.setenv("GEMINI_API_KEY", "")

    _patch_litellm(monkeypatch)
    _patch_hashes(monkeypatch)
    _patch_jinja(monkeypatch)
    _ensure_demo_user()

    yield


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
