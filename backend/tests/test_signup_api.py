import uuid

import pytest
from app.db import SessionLocal
from app.main import app
from app.services.user_service import get_user_by_username
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_signup_endpoint():
    username = f"signup_{uuid.uuid4().hex[:8]}"
    payload = {"username": username, "password": "SignUpPass123!", "email": f"{username}@example.com", "display_name": "Signup Test"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/signup", json=payload)
        assert resp.status_code == 201

        cookies = resp.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert "csrf_token" in cookies

    # verify user exists in DB and cleanup
    async with SessionLocal() as session:
        user = await get_user_by_username(session, username)
        assert user is not None
        await session.delete(user)
        await session.commit()
