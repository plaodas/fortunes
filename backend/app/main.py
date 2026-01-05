from app.api.v1.router import api_router
from app.middleware import CSRFMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fortunes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSRF protection (double submit cookie). CSRF cookie is created on safe requests.
app.add_middleware(CSRFMiddleware)

app.include_router(api_router, prefix="/api/v1")
