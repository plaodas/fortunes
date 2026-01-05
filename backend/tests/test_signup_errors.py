import uuid

import pytest
from app.db import SessionLocal
from app.main import app
from app.services.user_service import get_user_by_username
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_signup_duplicate_email():
    username1 = f"dup_{uuid.uuid4().hex[:8]}"
    username2 = f"dup2_{uuid.uuid4().hex[:8]}"
    email = f"{username1}@example.com"

    payload1 = {"username": username1, "password": "Pwd12345!", "email": email}
    payload2 = {"username": username2, "password": "Pwd12345!", "email": email}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post("/api/v1/auth/signup", json=payload1)
        assert r1.status_code == 201

        r2 = await ac.post("/api/v1/auth/signup", json=payload2)
        # duplicate email should be rejected with 400
        assert r2.status_code == 400

    # cleanup created user
    async with SessionLocal() as session:
        user = await get_user_by_username(session, username1)
        if user:
            await session.delete(user)
            await session.commit()


@pytest.mark.asyncio
async def test_signup_invalid_email():
    username = f"badmail_{uuid.uuid4().hex[:8]}"
    payload = {"username": username, "password": "Pwd12345!", "email": "not-an-email"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/signup", json=payload)
        # Pydantic validation should return 422 for invalid email
        assert resp.status_code == 422
