import json
import logging
import os
from typing import Any, List, cast

from app import db, models
from app.dtos.inputs.analyze_request import AnalyzeRequest
from app.dtos.outputs.analysis_out import AnalysisOut

# adapter for provider switching
from arq import create_pool as arq_create_pool
from arq.connections import RedisSettings as ArqRedisSettings
from arq.jobs import Job
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Use a module-level Depends wrapper to satisfy ruff B008
get_db_dependency = Depends(db.get_db)

logger = logging.getLogger("uvicorn")

app = FastAPI(title="Fortunes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check endpoint.
    軽量な Liveness
    Returns 200 OK with status "ok".
    """
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """Readiness probe: check DB and Redis connectivity.
    依存サービスの確認用
    Returns 200 when both are reachable, otherwise 503 with details.
    """
    checks: dict = {"db": False, "redis": False}
    details: dict = {}

    # Check Postgres via async engine
    try:
        async with db.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = True
    except Exception as e:
        details["db_error"] = str(e)

    # Check Redis via aioredis (use ARQ_REDIS_URL if present)
    try:
        # import here to keep module import lightweight if aioredis absent
        import aioredis

        redis_url = os.getenv("ARQ_REDIS_URL")
        r = aioredis.from_url(redis_url)
        try:
            pong = await r.ping()
            if pong:
                checks["redis"] = True
        finally:
            await r.close()
            # aioredis v2 uses wait_closed
            if hasattr(r, "wait_closed"):
                await r.wait_closed()
    except Exception as e:
        details["redis_error"] = str(e)

    if all(checks.values()):
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail={"status": "not ready", "checks": checks, "details": details})


@app.post("/analyze/enqueue")
async def analyze_enqueue(req: AnalyzeRequest):
    """Enqueue an analysis job via Arq and return the job id."""
    pool = await arq_create_pool(ArqRedisSettings(host="redis"))
    try:
        job = await pool.enqueue_job(
            "app.tasks.process_analysis",
            req.name_sei,
            req.name_mei,
            req.birth_date,
            int(req.birth_hour),
        )
        if job is None:
            raise HTTPException(status_code=500, detail={"error": "failed to enqueue job"})
        return {"job_id": job.job_id}
    finally:
        await pool.close()


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Return status and result (if available) for an Arq job id."""
    pool = await arq_create_pool(ArqRedisSettings(host="redis"))
    try:
        job = Job(job_id, pool)
        status = await job.status()
        res = None
        try:
            info = await job.result_info()
            if info:
                res = info.result
        except Exception:
            res = None

        return {"job_id": job_id, "status": str(status), "result": res}
    finally:
        await pool.close()


@app.get("/analyses", response_model=List[AnalysisOut])
async def list_analyses(limit: int = 50, db: AsyncSession = get_db_dependency):
    """Return recent analyses ordered by newest first."""
    # AsyncSession path
    stmt = select(models.Analysis).order_by(models.Analysis.id.desc()).limit(limit)
    res = await db.execute(stmt)
    qs = res.scalars().all()

    out = []
    for a in qs:
        result_name_val: Any = json.loads(a.result_name) if isinstance(a.result_name, str) else cast(Any, a.result_name)
        result_birth_val: Any = json.loads(a.result_birth) if isinstance(a.result_birth, str) else cast(Any, a.result_birth)
        out.append(
            AnalysisOut(
                id=cast(int, a.id),
                name=cast(str, a.name),
                birth_date=a.birth_date.isoformat(),
                birth_hour=cast(int, a.birth_hour),
                result_name=cast(dict, result_name_val),
                result_birth=cast(dict, result_birth_val),
                summary=cast(str, a.summary),
                detail=cast(str, a.detail),
                created_at=a.created_at.isoformat() if a.created_at else None,
            )
        )
    return out


@app.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: AsyncSession = get_db_dependency):
    """Delete an analysis by ID."""

    stmt = select(models.Analysis).where(models.Analysis.id == analysis_id).limit(1)
    res = await db.execute(stmt)
    obj = res.scalar_one_or_none()
    if not obj:
        return {"status": "not found"}
    await db.delete(obj)
    await db.commit()
    return {"status": "deleted"}
