import os

from app.api.v1.router import api_router
from app.middleware import CSRFMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fortunes API")

# Allow origins can be configured via FRONTEND_ORIGINS env var (comma-separated).
# When using cookies with cross-site requests, do NOT use '*' as allow_origins; set specific origins.
frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000")
if frontend_origins.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in frontend_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF protection (double submit cookie). CSRF cookie is created on safe requests.
app.add_middleware(CSRFMiddleware)

app.include_router(api_router, prefix="/api/v1")
