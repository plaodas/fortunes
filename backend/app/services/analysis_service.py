# app/services/analysis_service.py
from typing import List

from app import models
from app.schemas.outputs.analysis_out import AnalysisOut
from app.utils.dto import dto_list
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AnalysisService:
    async def list_analyses(self, db: AsyncSession, limit: int = 50) -> List[AnalysisOut]:
        stmt = select(models.Analysis).order_by(models.Analysis.id.desc()).limit(limit)
        res = await db.execute(stmt)
        rows = res.scalars().all()

        return dto_list(rows, AnalysisOut)

    async def delete_analysis(self, db: AsyncSession, analysis_id: int) -> bool:
        stmt = select(models.Analysis).where(models.Analysis.id == analysis_id)
        res = await db.execute(stmt)
        obj = res.scalar_one_or_none()

        if not obj:
            return False

        await db.delete(obj)
        await db.commit()
        return True
