import secrets
from datetime import timedelta

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


@router.post("/login", response_model=TokenOut)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = oauth2_form):
    # NOTE: 現時点ではDB接続を行わず、受け取った username を subject にしたトークンを返します。
    # TODO: 実際は DB でユーザ確認、パスワード検証を行うこと。
    username = form_data.username

    access_token = auth.create_access_token(subject=username, expires_delta=timedelta(minutes=15))
    refresh_token = auth.create_refresh_token(subject=username)

    # Set HttpOnly cookies for SPA usage
    response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="lax")

    # Create CSRF token (double-submit). This cookie is readable by JS so frontend can set X-CSRF-Token header.
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie("csrf_token", csrf_token, httponly=False, secure=False, samesite="lax")

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
    response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="lax")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "logged out"}


@router.get("/me")
async def me(username: str = Depends(auth.get_current_username)):
    return {"username": username}
