from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze():
    payload = {"name": "太郎", "birth_date": "1990-01-01", "birth_hour": 12}
    r = client.post("/analyze", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "result" in body
    assert body["result"]["nameAnalysis"]["summary"] == "努力家で晩年安定"
