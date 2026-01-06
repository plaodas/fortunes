import os
import secrets
from datetime import timedelta
from typing import Literal, Optional, cast

from app import auth
from app.db import get_db
from app.services import mailer
from app.services.user_service import create_user, get_user_by_id, get_user_by_username
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])

# Restrict samesite to the allowed literal values so type checkers are satisfied.
CookieSameSite = Literal["lax", "strict", "none"]


# Module-level dependency to avoid calling `Depends()` in function defaults (ruff B008)
oauth2_form = Depends(OAuth2PasswordRequestForm)
asyncSession = Depends(get_db)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SignupIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    display_name: str | None = None


def _resolve_samesite(value: str | None) -> Optional[CookieSameSite]:
    if value is None:
        return None
    v = value.lower()
    allowed = ("lax", "strict", "none")
    if v not in allowed:
        v = "lax"
    return cast(CookieSameSite, v)


@router.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = oauth2_form, db: AsyncSession = asyncSession):
    # Validate credentials against the database
    username = form_data.username
    # lookup user in db
    user = await get_user_by_username(db, username)
    # If user not found or password invalid, return 401
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    # Use immutable user id as the JWT `sub` so username changes won't invalidate tokens
    access_token = auth.create_access_token(subject=str(user.id), expires_delta=timedelta(minutes=15))
    refresh_token = auth.create_refresh_token(subject=str(user.id))

    # Cookie attributes configurable by env for dev/prod differences
    cookie_secure = os.getenv("JWT_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    cookie_samesite = _resolve_samesite(os.getenv("JWT_COOKIE_SAMESITE", "lax"))  # 'lax' or 'none' recommended for cross-site
    cookie_domain = os.getenv("JWT_COOKIE_DOMAIN") or None

    # Set HttpOnly cookies for SPA usage
    response.set_cookie("access_token", access_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)

    # Create CSRF token (double-submit). This cookie is readable by JS so frontend can set X-CSRF-Token header.
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie("csrf_token", csrf_token, httponly=False, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)

    # Do not return tokens in JSON; rely on HttpOnly cookies and CSRF cookie.
    return {"username": user.username, "email": user.email}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(response: Response, payload: SignupIn, db: AsyncSession = asyncSession):
    # email is required by the payload type
    try:
        user = await create_user(db, username=payload.username, password=payload.password, email=payload.email, display_name=payload.display_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None

    # set tokens subject to user.id (immutable)
    access_token = auth.create_access_token(subject=str(user.id))
    refresh_token = auth.create_refresh_token(subject=str(user.id))

    cookie_secure = os.getenv("JWT_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    cookie_samesite = _resolve_samesite(os.getenv("JWT_COOKIE_SAMESITE", "lax"))
    cookie_domain = os.getenv("JWT_COOKIE_DOMAIN") or None

    response.set_cookie("access_token", access_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)

    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie("csrf_token", csrf_token, httponly=False, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)

    # Send confirmation email (non-blocking behavior could be added later)
    try:
        # create a short-lived email confirmation token using user id as subject
        token = auth.create_email_token(subject=str(user.id))
        confirm_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000") + f"/confirm-email?token={token}"
        # payload.email is required by the request model, use it to satisfy static typing
        mailer.send_confirmation_email(payload.email, confirm_url)
    except Exception:
        # Do not fail signup for email sending errors; log instead.
        import logging

        logging.exception("Failed to send confirmation email")

    # Do not return tokens in JSON; rely on HttpOnly cookies and CSRF cookie.
    return {"username": user.username, "email": user.email}


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    payload = auth.decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    # Defensive check: ensure subject is present even if decode_token performs validation.
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing subject")
    access_token = auth.create_access_token(subject=username)
    cookie_secure = os.getenv("JWT_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    cookie_samesite = _resolve_samesite(os.getenv("JWT_COOKIE_SAMESITE", "lax"))
    cookie_domain = os.getenv("JWT_COOKIE_DOMAIN") or None
    response.set_cookie("access_token", access_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    # No token in JSON response; client should rely on cookies.
    return {"detail": "refreshed"}


@router.get("/confirm-email")
async def confirm_email(token: str | None = None, db: AsyncSession = asyncSession):
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing token")
    payload = auth.decode_token(token)
    if payload.get("type") != "confirm_email":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload")

    # subject is the user id (string). Update by id when possible.
    try:
        user_id = int(subject)
        q = await db.execute(
            text('UPDATE "users" SET email_verified = TRUE WHERE id = :user_id RETURNING id'),
            {"user_id": user_id},
        )
    except Exception:
        # Fallback: treat subject as username
        q = await db.execute(
            text('UPDATE "users" SET email_verified = TRUE WHERE username = :username RETURNING id'),
            {"username": subject},
        )
    row = q.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.commit()
    return {"detail": "email confirmed"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "logged out"}


@router.get("/me")
async def me(db: AsyncSession = asyncSession, user_id: int = Depends(auth.get_current_userid)):
    # Return basic user info including whether their email is verified.
    # Frontend should use `email_verified` to decide whether to treat the session
    # as fully logged-in for protected flows.
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"username": user.username, "email": user.email, "email_verified": bool(user.email_verified)}


class UpdateIn(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


@router.post("/update")
async def update_profile(payload: UpdateIn, db: AsyncSession = asyncSession, user_id: int = Depends(auth.get_current_userid)):
    # fetch current user
    from app.services.user_service import get_user_by_email, get_user_by_username

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # If username changed, ensure uniqueness
    if payload.username and payload.username != user.username:
        existing = await get_user_by_username(db, payload.username)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
        user.username = payload.username

    # If email changed, ensure uniqueness
    if payload.email and payload.email != user.email:
        existing_email = await get_user_by_email(db, payload.email)
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
        user.email = payload.email

    db.add(user)
    await db.commit()
    await db.refresh(user)
    # Issue rotated tokens so client continues working without forcing re-login.
    cookie_secure = os.getenv("JWT_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    cookie_samesite = _resolve_samesite(os.getenv("JWT_COOKIE_SAMESITE", "lax"))
    cookie_domain = os.getenv("JWT_COOKIE_DOMAIN") or None

    access_token = auth.create_access_token(subject=str(user.id))
    refresh_token = auth.create_refresh_token(subject=str(user.id))

    # Set HttpOnly cookies for SPA usage
    response = Response()
    response.set_cookie("access_token", access_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    # rotate CSRF token (readable by JS)
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie("csrf_token", csrf_token, httponly=False, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)

    # Attach cookies to a proper JSON response and return new token info plus profile
    from fastapi.responses import JSONResponse

    payload_out = {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "email": user.email,
    }
    json_resp = JSONResponse(payload_out)
    # copy cookies onto the JSONResponse
    json_resp.set_cookie("access_token", access_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    json_resp.set_cookie("refresh_token", refresh_token, httponly=True, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    json_resp.set_cookie("csrf_token", csrf_token, httponly=False, secure=cookie_secure, samesite=cookie_samesite, domain=cookie_domain)
    return json_resp


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(payload: ChangePasswordIn, db: AsyncSession = asyncSession, user_id: int = Depends(auth.get_current_userid)):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # verify current password
    if not auth.verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="current password is incorrect")

    # set new password hash
    user.password_hash = auth.get_password_hash(payload.new_password)
    db.add(user)
    await db.commit()
    return {"detail": "password changed"}
