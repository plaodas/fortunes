import pytest
from app import tasks as tasks_module
from app.main import app
from app.models import LLMResponse
from httpx import ASGITransport, AsyncClient

URL_PREFIX = "/api/v1"


@pytest.mark.anyio
async def test_analyze_enqueue_returns_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePool:
        def __init__(self):
            self.closed = False

        async def enqueue_job(self, *args, **kwargs):
            class J:
                job_id = "fake-job-1"

            return J()

        async def aclose(self):
            self.closed = True

    async def fake_create_pool(*args, **kwargs):
        return FakePool()

    monkeypatch.setattr("app.services.job_service.create_pool", fake_create_pool)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(URL_PREFIX + "/analyze/enqueue", json={"name_sei": "太", "name_mei": "郎", "birth_date": "1990-01-01", "birth_hour": 12})

    assert r.status_code == 200
    assert r.json().get("job_id") == "fake-job-1"


@pytest.mark.anyio
async def test_get_job_status_returns_complete_and_result(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeJob:
        def __init__(self, job_id, pool):
            self.job_id = job_id

        async def status(self):
            return "complete"

        async def result_info(self):
            class R:
                result = {"id": 1, "name": "太 郎"}

            return R()

    async def fake_create_pool(*args, **kwargs):
        class P:
            async def aclose(self):
                pass

        return P()

    monkeypatch.setattr("app.services.job_service.create_pool", fake_create_pool)
    monkeypatch.setattr("app.services.job_service.Job", FakeJob)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(URL_PREFIX + "/jobs/fake-job-1")

    assert r.status_code == 200
    body = r.json()
    assert body["status"].lower().startswith("jobstatus") or body["status"] == "complete"
    assert body["result"] == {"id": 1, "name": "太 郎"}


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLLMResponse:
        def __init__(self, provider, model):
            self.provider = provider
            self.model = model

        async def make_analysis(self, system_prompt: str, user_prompt: str) -> LLMResponse:
            message = {
                "role": "assistant",
                "images": [],
                "content": "あなたは、太陽のように温かく…",
            }
            choices = [{"index": 0, "message": message, "finish_reason": "stop"}]
            raw = {
                "id": "jANVaYGXApSR0-kP6Zbz6Ak",
                "model": "gemini-2.5-flash-lite",
                "object": "chat.completion",
                "choices": choices,
                "created": 1767179146,
                "system_fingerprint": None,
            }

            return LLMResponse(
                id=1,
                request_id=None,
                provider=self.provider,
                model=self.model,
                model_version=None,
                response_id="4AtKaYDXNIWU1e8P1v6H-A0",
                prompt_hash=None,
                response_text="人生という桃源郷を巡る旅の途中…",
                usage={"completion_tokens": 78, "completion_tokens_details": None},
                raw=raw,
                created_at="2025-12-23 03:26:25.385178+00",
            )

    monkeypatch.setattr(
        tasks_module.litellm_adapter,
        "LiteLlmAdapter",
        FakeLLMResponse,
    )


@pytest.fixture
def fake_session() -> type:
    class FakeSession:
        def __init__(self):
            self.added = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, model, key):
            class K:
                def __init__(self, ch):
                    self.char = ch
                    self.strokes_min = 4 if ch == "太" else 9

            return K(key)

        def add(self, obj):
            obj.id = 99999
            self.added = obj

        async def commit(self):
            return

        async def rollback(self):
            return

        async def close(self):
            return

    return FakeSession


@pytest.fixture
def fake_session_local(monkeypatch: pytest.MonkeyPatch, fake_session: type) -> None:
    def fake_sessionlocal():
        return fake_session()

    monkeypatch.setattr(tasks_module.db, "SessionLocal", fake_sessionlocal)


@pytest.mark.anyio
async def test_process_analysis_creates_and_returns_id(fake_llm, fake_session_local) -> None:
    res = await tasks_module.process_analysis({}, "太", "郎", "1990-01-01", 12)

    assert isinstance(res, dict)
    assert res.get("id") == 99999
    assert "name" in res
