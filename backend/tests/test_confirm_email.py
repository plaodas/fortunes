import asyncio
from urllib.parse import parse_qs, urlparse

from app.db import SessionLocal
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


def test_signup_and_confirm_email(monkeypatch):
    captured: dict = {}

    def fake_send(to_address: str, confirm_url: str, subject: str | None = None) -> None:
        captured["url"] = confirm_url

    monkeypatch.setattr("app.services.mailer.send_confirmation_email", fake_send)

    username = "test_confirm_user"
    email = f"{username}@example.com"
    payload = {"username": username, "password": "password123", "email": email, "display_name": "Test"}

    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/signup", json=payload)
            assert resp.status_code == 201
            assert "url" in captured

            parsed = urlparse(captured["url"])
            qs = parse_qs(parsed.query)
            token = qs.get("token", [None])[0]
            assert token is not None

            # verify DB record is initially unverified
            async with SessionLocal() as session:
                r = await session.execute(text('SELECT email_verified FROM "user" WHERE username = :username'), {"username": username})
                val = r.scalar_one_or_none()
                assert val is False

            # call confirmation endpoint
            resp2 = await client.get(f"/api/v1/auth/confirm-email?token={token}")
            assert resp2.status_code == 200
            assert resp2.json().get("detail") == "email confirmed"

            async with SessionLocal() as session:
                r = await session.execute(text('SELECT email_verified FROM "user" WHERE username = :username'), {"username": username})
                val = r.scalar_one_or_none()
                assert val is True

    asyncio.run(run())


def test_confirm_email_missing_token():
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/confirm-email")
            assert resp.status_code == 400

    asyncio.run(run())


def test_confirm_email_invalid_token():
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/confirm-email?token=invalid.token.value")
            assert resp.status_code == 401

    asyncio.run(run())
