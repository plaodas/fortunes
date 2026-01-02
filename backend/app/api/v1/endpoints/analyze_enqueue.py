# app/api/v1/endpoints/analyze_enqueue.py
from app import db, models
from app.schemas.inputs.analyze_request import AnalyzeRequest
from app.services.job_service import JobService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analyze", tags=["analysis"])
job_service = JobService()

get_db = Depends(db.get_db)


@router.post("/enqueue")
async def analyze_enqueue(req: AnalyzeRequest, db: AsyncSession = get_db) -> dict:
    if not await validate_kanji_characters(req.name_sei, req.name_mei, db):
        raise HTTPException(status_code=422, detail="One or more characters not found in Kanji table")

    job = await job_service.enqueue_analysis(
        req.name_sei,
        req.name_mei,
        req.birth_date,
        int(req.birth_hour),
    )
    if job is None:
        raise HTTPException(status_code=500, detail="failed to enqueue job")
    return {"job_id": job.job_id}


# req.name_seiとreq.name_meiに含まれる文字がKanjiテーブルに存在しない場合Falseを返す
async def validate_kanji_characters(name_sei: str, name_mei: str, db: AsyncSession) -> bool:
    # name_sei + name_meiの文字について重複を排除してList化
    chars = list(set(name_sei + name_mei))
    # select char from kanji where char in (:char1, :char2, ...) で一括取得
    stmt = select(models.Kanji).where(models.Kanji.char.in_(chars))
    kanji = await db.execute(stmt)
    # 取得文字数がcharsの長さと一致しなければ存在しない文字があると判断
    stored_chars = {row[0].char for row in kanji.fetchall()}
    return len(stored_chars) == len(chars)
