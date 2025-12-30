import asyncio

import pytest
from app import tasks as tasks_module
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_analyze_enqueue_returns_job_id(monkeypatch):
    class FakePool:
        def __init__(self):
            self.closed = False

        async def enqueue_job(self, *args, **kwargs):
            class J:
                job_id = "fake-job-1"

            return J()

        async def close(self):
            self.closed = True

    async def fake_create_pool(*args, **kwargs):
        return FakePool()

    monkeypatch.setattr("app.main.arq_create_pool", fake_create_pool)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/analyze/enqueue", json={"name_sei": "太", "name_mei": "郎", "birth_date": "1990-01-01", "birth_hour": 12})

    assert r.status_code == 200
    assert r.json().get("job_id") == "fake-job-1"


@pytest.mark.anyio
async def test_get_job_status_returns_complete_and_result(monkeypatch):
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
            async def close(self):
                pass

        return P()

    monkeypatch.setattr("app.main.arq_create_pool", fake_create_pool)
    monkeypatch.setattr("app.main.Job", FakeJob)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/jobs/fake-job-1")

    assert r.status_code == 200
    body = r.json()
    assert body["status"].lower().startswith("jobstatus") or body["status"] == "complete"
    assert body["result"] == {"id": 1, "name": "太 郎"}


@pytest.mark.anyio
async def test_process_analysis_creates_and_returns_id(monkeypatch):
    # Patch litellm adapter to return deterministic strings
    monkeypatch.setattr(tasks_module.litellm_adapter, "make_analysis_detail", lambda *a, **k: asyncio.sleep(0) or "detail")
    monkeypatch.setattr(tasks_module.litellm_adapter, "make_analysis_summary", lambda *a, **k: asyncio.sleep(0) or "summary")

    # Fake async session context manager
    class FakeSession:
        def __init__(self):
            self.added = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, model, key):
            # return an object with strokes_min
            class K:
                def __init__(self, ch):
                    self.char = ch
                    self.strokes_min = 4 if ch == "太" else 9

            return K(key)

        def add(self, obj):
            # simulate ORM assigning id on add
            obj.id = 42
            self.added = obj

        async def commit(self):
            return True

    def fake_sessionlocal():
        return FakeSession()

    monkeypatch.setattr(tasks_module.db, "SessionLocal", fake_sessionlocal)

    res = await tasks_module.process_analysis({}, "太", "郎", "1990-01-01", 12)
    assert isinstance(res, dict)
    assert res.get("id") == 42
    assert "name" in res
