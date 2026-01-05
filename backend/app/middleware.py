import secrets
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CSRf_SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method.upper()
        csrf_cookie = request.cookies.get("csrf_token")

        # For safe methods, ensure a CSRF cookie exists; if not, set one in the response
        if method in CSRf_SAFE_METHODS:
            response = await call_next(request)
            if not csrf_cookie:
                token = secrets.token_urlsafe(32)
                response.set_cookie("csrf_token", token, httponly=False, secure=False, samesite="lax")
            return response

        # For unsafe methods, validate header matches cookie
        csrf_header = request.headers.get("x-csrf-token") or request.headers.get("x-xsrf-token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return Response(status_code=403, content="CSRF token missing or invalid")

        return await call_next(request)
