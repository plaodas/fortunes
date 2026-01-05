import os
import secrets
from datetime import timedelta
from typing import Literal, Optional, cast

from app import auth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

# Module-level dependency to avoid calling `Depends()` in function defaults (ruff B008)
oauth2_form = Depends(OAuth2PasswordRequestForm)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Restrict samesite to the allowed literal values so type checkers are satisfied.
CookieSameSite = Literal["lax", "strict", "none"]


def _resolve_samesite(value: str | None) -> Optional[CookieSameSite]:
    if value is None:
        return None
    v = value.lower()
    allowed = ("lax", "strict", "none")
    if v not in allowed:
        v = "lax"
    return cast(CookieSameSite, v)


@router.post("/login", response_model=TokenOut)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = oauth2_form):
    # NOTE: 現時点ではDB接続を行わず、受け取った username を subject にしたトークンを返します。
    # TODO: 実際は DB でユーザ確認、パスワード検証を行うこと。
    username = form_data.username

    access_token = auth.create_access_token(subject=username, expires_delta=timedelta(minutes=15))
    refresh_token = auth.create_refresh_token(subject=username)

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

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenOut)
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
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "logged out"}


@router.get("/me")
async def me(username: str = Depends(auth.get_current_username)):
    return {"username": username}
