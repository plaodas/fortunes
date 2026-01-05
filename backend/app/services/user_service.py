from typing import Optional

from app.auth import get_password_hash
from app.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    q = await db.execute(select(User).where(User.id == user_id))
    return q.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    q = await db.execute(select(User).where(User.username == username))
    return q.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    if not email:
        return None
    q = await db.execute(select(User).where(User.email == email))
    return q.scalars().first()


async def create_user(db: AsyncSession, username: str, password: str, email: Optional[str] = None, display_name: Optional[str] = None) -> User:
    # Check uniqueness
    existing = await get_user_by_username(db, username)
    if existing:
        raise ValueError("username already exists")
    if email:
        existing_email = await get_user_by_email(db, email)
        if existing_email:
            raise ValueError("email already exists")

    pw_hash = get_password_hash(password)
    user = User(username=username, email=email, password_hash=pw_hash, display_name=display_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
