# app/services/analysis_service.py
from typing import List

from app import models
from app.schemas.outputs.analysis_out import AnalysisOut
from app.utils.dto import dto_list
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class AnalysisService:
    async def list_analyses(self, db: AsyncSession, limit: int = 50) -> List[AnalysisOut]:
        # stmt = select(models.Analysis).order_by(models.Analysis.id.desc()).limit(limit)

        # SQL: (birth_datetime AT TIME ZONE timezone) yields timestamp without tz in that zone,
        # so wrap with date() / extract(hour ...)
        local_ts = func.timezone(models.Analysis.birth_tz, models.Analysis.birth_datetime)  # timezone(zone, timestamptz)

        stmt = (
            select(
                models.Analysis.id,
                models.Analysis.name,
                func.date(local_ts).label("birth_date"),
                cast(func.extract("hour", local_ts), Integer).label("birth_hour"),
                models.Analysis.birth_tz,
                models.Analysis.result_birth,
                models.Analysis.result_name,
                models.Analysis.summary,
                models.Analysis.detail,
                models.Analysis.created_at,
            )
            .order_by(models.Analysis.created_at.desc())
            .limit(limit)
        )

        res = await db.execute(stmt)
        rows = [r._mapping for r in res]
        # rows[i]["birth_date"] -> date, rows[i]["birth_hour"] -> int, rows[i]["birth_tz"] -> str

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
