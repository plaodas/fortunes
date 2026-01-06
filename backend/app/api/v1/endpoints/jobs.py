# app/api/v1/endpoints/jobs.py
from app.services.job_service import JobService
from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])
job_service = JobService()


@router.get("/{job_id}")
async def get_job_status(job_id: str) -> dict:
    # public endpoint: return job status (authorization handled elsewhere if needed)
    return await job_service.get_job_status(job_id)
