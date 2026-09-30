# app/api/v1/endpoints/analyze_enqueue.py
from app import auth, db, models
from app.schemas.inputs.analyze_request import AnalyzeRequest
from app.services.job_service import JobService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analyze", tags=["analysis"])
job_service = JobService()

get_db = Depends(db.get_db)


@router.post("/enqueue")
async def analyze_enqueue(req: AnalyzeRequest, db: AsyncSession = get_db, user_id: int = Depends(auth.get_current_userid)) -> dict:
    if not await validate_kanji_characters(req.name_sei, req.name_mei, db):
        raise HTTPException(status_code=422, detail="康熙画数が不明な文字があるため鑑定できません")

    job = await job_service.enqueue_analysis(
        user_id,
        req.name_sei,
        req.name_mei,
        req.birth_date.isoformat(),  # ArqはRedisにジョブ引数をシリアライズして保存するので、"YYYY-MM-DD"形式の文字列として渡す（AnalyzeRequestは日付のバリデーションのためにdate型指定）
        int(req.birth_hour),
        req.sex,
        req.birth_tz,
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
    stored = {row[0].char: row[0] for row in kanji.fetchall()}
    return all(ch in stored and stored[ch].strokes_kangxi is not None for ch in chars)
