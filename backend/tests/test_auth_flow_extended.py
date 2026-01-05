import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_refresh_logout_flow():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Login
        resp = await ac.post("/api/v1/auth/login", data={"username": "demo", "password": "demo"})
        assert resp.status_code == 200

        # Refresh should issue a new access_token cookie
        refresh_resp = await ac.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.cookies or "access_token" in ac.cookies

        # Logout should clear cookies; subsequent protected call fails
        logout_resp = await ac.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200

        me = await ac.get("/api/v1/auth/me")
        assert me.status_code == 401


@pytest.mark.asyncio
async def test_invalid_access_token_returns_401():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Use invalid bearer token
        me = await ac.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert me.status_code == 401


@pytest.mark.asyncio
async def test_invalid_refresh_token_returns_401():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Manually set an invalid refresh token cookie
        ac.cookies.set("refresh_token", "badtoken")
        resp = await ac.post("/api/v1/auth/refresh")
        assert resp.status_code == 401
