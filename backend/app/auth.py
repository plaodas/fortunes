import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.db import get_db
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
EMAIL_CONFIRM_EXPIRE_HOURS = int(os.getenv("EMAIL_CONFIRM_EXPIRE_HOURS", "24"))

async_session = Depends(get_db)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # bcrypt has a 72-byte input limit; proactively check and raise a clear error.
    b = password.encode("utf-8")
    if len(b) > 72:
        raise ValueError("password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])")

    try:
        return pwd_context.hash(password)
    except Exception:
        # If bcrypt backend is unavailable or fails (some environments ship
        # an incompatible 'bcrypt' package), fall back to pbkdf2_sha256 to
        # avoid failing user signup. Log the exception for diagnostics.
        logging.exception("bcrypt hashing failed; falling back to pbkdf2_sha256")
        return pbkdf2_sha256.hash(password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # JWT 'exp' must be a numeric timestamp. Store as int seconds since epoch.
    to_encode.update({"exp": str(int(expire.timestamp()))})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject, "type": "refresh"}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": str(int(expire.timestamp()))})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_email_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject, "type": "confirm_email"}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=EMAIL_CONFIRM_EXPIRE_HOURS))
    to_encode.update({"exp": str(int(expire.timestamp()))})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Ensure token contains a subject ('sub'). Centralized validation
        # helps callers rely on decode_token to raise on malformed tokens.
        if not payload.get("sub"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload: missing subject")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from None


async def get_current_userid(request: Request, db: AsyncSession = async_session) -> int:
    # Prefer Authorization: Bearer <token> header, fallback to 'access_token' cookie
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # `sub` is now expected to be the numeric user id (as a string). Resolve
    # the user id to a username for legacy callers that expect a username.
    try:
        user_id = int(subject)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from None

    # user = await get_user_by_id(db, user_id)
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user_id
