import secrets
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CSRf_SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exempt_paths: list[str] | None = None):
        super().__init__(app)
        # Default exempt paths (auth endpoints + docs/openapi)
        # login から CSRF チェックを除外するのは一般的に許容される範囲
        self.exempt_paths = exempt_paths or [
            "/api/v1/auth/signup",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
            "/openapi.json",
            "/docs",
            "/redoc",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method.upper()
        path = request.url.path
        csrf_cookie = request.cookies.get("csrf_token")

        # For safe methods, ensure a CSRF cookie exists; if not, set one in the response
        if method in CSRf_SAFE_METHODS:
            # Always set/overwrite the CSRF cookie on safe requests so the
            # client-side double-submit token remains in sync with the server.
            response = await call_next(request)
            token = secrets.token_urlsafe(32)
            response.set_cookie("csrf_token", token, httponly=False, secure=False, samesite="lax")
            return response

        # Skip CSRF check for exempted paths (e.g., login/refresh)
        for p in self.exempt_paths:
            if path.startswith(p):
                return await call_next(request)

        # For unsafe methods, validate header matches cookie
        csrf_header = request.headers.get("x-csrf-token") or request.headers.get("x-xsrf-token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return Response(status_code=403, content="CSRF token missing or invalid")

        return await call_next(request)
