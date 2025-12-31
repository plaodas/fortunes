# app/api/v1/endpoints/analyses.py
from app import db
from app.services.analysis_service import AnalysisService
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analyses", tags=["analysis"])
analysis_service = AnalysisService()

get_db = Depends(db.get_db)


@router.get("")
async def list_analyses(limit: int = 50, db: AsyncSession = get_db):
    return await analysis_service.list_analyses(db, limit)


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: int, db: AsyncSession = get_db):
    ok = await analysis_service.delete_analysis(db, analysis_id)
    return {"status": "deleted" if ok else "not found"}
