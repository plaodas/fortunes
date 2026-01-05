import uuid

import pytest
from app.db import SessionLocal
from app.services.user_service import create_user, get_user_by_username


@pytest.mark.asyncio
async def test_create_and_get_user():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "Secret123!"
    email = f"{username}@example.com"

    async with SessionLocal() as session:
        # create user
        user = await create_user(session, username=username, password=password, email=email, display_name="Test User")
        assert user is not None
        assert user.username == username
        assert user.email == email
        assert user.password_hash != password

        # retrieve
        fetched = await get_user_by_username(session, username)
        assert fetched is not None
        assert fetched.id == user.id

        # cleanup
        await session.delete(user)
        await session.commit()
