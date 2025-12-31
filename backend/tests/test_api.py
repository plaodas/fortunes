from typing import Any, AsyncGenerator

import pytest
from app import db as db_module
from app.main import app
from httpx import ASGITransport, AsyncClient

URL_PREFIX = "/api/v1"


@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(URL_PREFIX + "/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


class FakeResult:
    def __init__(self, rows: list | None = None):
        # rows: None | single object | list/tuple of objects
        self._rows = rows

    def scalars(self) -> object:
        class S:
            def __init__(self, rows):
                self._rows = rows

            def all(self) -> list:
                if self._rows is None:
                    return []
                return list(self._rows) if isinstance(self._rows, (list, tuple)) else [self._rows]

        return S(self._rows)

    def scalar_one_or_none(self) -> object | None:
        if self._rows is None:
            return None
        if isinstance(self._rows, (list, tuple)):
            return self._rows[0] if self._rows else None
        return self._rows


class FakeAsyncSession:
    def __init__(self, query_result=None):
        self._query_result = query_result
        self.deleted = False
        self.committed = False

    async def execute(self, stmt):
        return FakeResult(self._query_result or [])

    async def delete(self, obj):
        self.deleted = True

    async def commit(self):
        self.committed = True


@pytest.mark.anyio
async def test_get_analyses_empty():
    # dependency override
    async def fake_get_db() -> AsyncGenerator[Any, Any]:
        yield FakeAsyncSession(query_result=[])

    app.dependency_overrides[db_module.get_db] = fake_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(URL_PREFIX + "/analyses")
    assert r.status_code == 200
    assert r.json() == []
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_analysis_not_found():
    async def fake_get_db():
        yield FakeAsyncSession(query_result=None)

    app.dependency_overrides[db_module.get_db] = fake_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.delete(URL_PREFIX + "/analyses/123")
    assert r.status_code == 200
    assert r.json() == {"status": "not found"}
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_analysis_deleted():
    fake_obj = type("O", (), {"id": 1})

    # dependency override
    async def fake_get_db():
        yield FakeAsyncSession(query_result=[fake_obj])

    app.dependency_overrides[db_module.get_db] = fake_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.delete(URL_PREFIX + "/analyses/1")
    assert r.status_code == 200
    assert r.json() == {"status": "deleted"}
    app.dependency_overrides.clear()
