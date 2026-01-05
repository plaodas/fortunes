import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_login_and_access_protected():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Login
        resp = await ac.post("/api/v1/auth/login", data={"username": "demo", "password": "demo"})
        assert resp.status_code == 200

        # Cookies should be set
        cookies = resp.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert "csrf_token" in cookies

        csrf = cookies.get("csrf_token")

        # Call protected endpoint with CSRF header
        prot = await ac.get("/api/v1/auth/me", headers={"x-csrf-token": csrf})
        assert prot.status_code == 200
        body = prot.json()
        assert body.get("username") == "demo"
