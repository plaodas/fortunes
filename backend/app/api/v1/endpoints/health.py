# app/api/v1/endpoints/health.py
import os

from app import db
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    checks = {"db": False, "redis": False}
    details = {}

    # DB check
    try:
        async with db.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = True
    except Exception as e:
        details["db_error"] = str(e)

    # Redis check
    try:
        import aioredis

        redis_url = os.getenv("ARQ_REDIS_URL")
        r = aioredis.from_url(redis_url)
        try:
            if await r.ping():
                checks["redis"] = True
        finally:
            await r.close()
            if hasattr(r, "wait_closed"):
                await r.wait_closed()
    except Exception as e:
        details["redis_error"] = str(e)

    if all(checks.values()):
        return {"status": "ready"}

    raise HTTPException(status_code=503, detail={"status": "not ready", "checks": checks, "details": details})
