# app/api/v1/router.py
from fastapi import APIRouter

from .endpoints import analyses, analyze_enqueue, health, jobs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jobs.router)
api_router.include_router(analyses.router)
api_router.include_router(analyze_enqueue.router)
