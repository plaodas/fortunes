import pytest
from app import db as db_module
from app import models
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.anyio
async def test_post_analyze():
    # Mock the DB session used inside the endpoint to avoid touching a real DB
    class FakeWriteSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add(self, obj):
            self.added = obj

        def commit(self):
            self.committed = True

        def get(self, model: models.Kanji, key: str):
            if key == "太":
                return model(char="太", strokes_min=4)
            elif key == "郎":
                return model(char="郎", strokes_min=9)
            else:
                return None

    orig_SessionLocal = db_module.SessionLocal
    try:
        db_module.SessionLocal = lambda: FakeWriteSession()
        payload = {"name_sei": "太", "name_mei": "郎", "birth_date": "1990-01-01", "birth_hour": 12}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/analyze", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert "result" in body
        assert body["result"]["name_analysis"]["soukaku"] == 13  # 4 + 9
    finally:
        db_module.SessionLocal = orig_SessionLocal


class FakeQuery:
    def __init__(self, result=None):
        self._result = result

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self

    def all(self):
        return self._result or []

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class FakeSession:
    def __init__(self, query_result=None):
        self._query_result = query_result
        self.deleted = False
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return FakeQuery(self._query_result)

    def delete(self, obj):
        self.deleted = True

    def commit(self):
        self.committed = True

    def add(self, obj):
        pass


@pytest.mark.anyio
async def test_get_analyses_empty():
    def fake_get_db():
        yield FakeSession(query_result=[])

    app.dependency_overrides[db_module.get_db] = fake_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/analyses")
    assert r.status_code == 200
    assert r.json() == []
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_analysis_not_found():
    def fake_get_db():
        yield FakeSession(query_result=None)

    app.dependency_overrides[db_module.get_db] = fake_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.delete("/analyses/123")
    assert r.status_code == 200
    assert r.json() == {"status": "not found"}
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_analysis_deleted():
    fake_obj = type("O", (), {"id": 1})

    def fake_get_db():
        yield FakeSession(query_result=fake_obj)

    app.dependency_overrides[db_module.get_db] = fake_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.delete("/analyses/1")
    assert r.status_code == 200
    assert r.json() == {"status": "deleted"}
    app.dependency_overrides.clear()
