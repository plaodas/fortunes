# app/api/v1/endpoints/analyze_enqueue.py
from app.schemas.inputs.analyze_request import AnalyzeRequest
from app.services.job_service import JobService
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analyze", tags=["analysis"])
job_service = JobService()


@router.post("/enqueue")
async def analyze_enqueue(req: AnalyzeRequest):
    job = await job_service.enqueue_analysis(
        req.name_sei,
        req.name_mei,
        req.birth_date,
        int(req.birth_hour),
    )
    if job is None:
        raise HTTPException(status_code=500, detail="failed to enqueue job")
    return {"job_id": job.job_id}
