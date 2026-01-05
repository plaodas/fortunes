# app/api/v1/router.py
from fastapi import APIRouter

from . import auth as auth_router_module
from .endpoints import analyses, analyze_enqueue, health, jobs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jobs.router)
api_router.include_router(analyses.router)
api_router.include_router(analyze_enqueue.router)

# authentication routes
api_router.include_router(auth_router_module.router)
