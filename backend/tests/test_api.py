from typing import Any, AsyncGenerator

import pytest
from app import db as db_module
from app.main import app

URL_PREFIX = "/api/v1"


@pytest.mark.anyio
async def test_health(async_client):
    r = await async_client.get(URL_PREFIX + "/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


class FakeResult:
    def __init__(self, rows: list | None = None):
        # rows: None | single object | list/tuple of objects
        self._rows = rows

    def scalar_one_or_none(self) -> object | None:
        if self._rows is None:
            return None
        if isinstance(self._rows, (list, tuple)):
            return self._rows[0] if self._rows else None
        return self._rows

    def __iter__(self):
        # Support iteration like SQLAlchemy Result where each item has a `_mapping` attribute
        if not self._rows:
            return iter(())

        rows = self._rows if isinstance(self._rows, (list, tuple)) else [self._rows]

        def to_row_obj(val):
            if hasattr(val, "_mapping"):
                return val
            if isinstance(val, dict):
                return type("_Row", (), {"_mapping": val})()
            # fallback: try to use __dict__ for attribute-based objects
            mapping = getattr(val, "__dict__", {}) or {}
            return type("_Row", (), {"_mapping": mapping})()

        return (to_row_obj(v) for v in rows)


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
async def test_get_analyses_empty(logged_in_client):
    # dependency override
    async def fake_get_db() -> AsyncGenerator[Any, Any]:
        yield FakeAsyncSession(query_result=[])

    app.dependency_overrides[db_module.get_db] = fake_get_db
    try:
        # perform a real login first so cookies/headers are set
        r = await logged_in_client.get(URL_PREFIX + "/analyses")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.pop(db_module.get_db, None)


@pytest.mark.anyio
async def test_delete_analysis_not_found(logged_in_client):
    async def fake_get_db():
        yield FakeAsyncSession(query_result=None)

    app.dependency_overrides[db_module.get_db] = fake_get_db
    try:
        r = await logged_in_client.delete(URL_PREFIX + "/analyses/123")
        assert r.status_code == 200
        assert r.json() == {"status": "not found"}
    finally:
        app.dependency_overrides.pop(db_module.get_db, None)


@pytest.mark.anyio
async def test_delete_analysis_deleted(logged_in_client):
    fake_obj = type("O", (), {"id": 1})

    # dependency override
    async def fake_get_db():
        yield FakeAsyncSession(query_result=[fake_obj])

    app.dependency_overrides[db_module.get_db] = fake_get_db
    try:
        r = await logged_in_client.delete(URL_PREFIX + "/analyses/1")
        assert r.status_code == 200
        assert r.json() == {"status": "deleted"}
    finally:
        app.dependency_overrides.pop(db_module.get_db, None)
