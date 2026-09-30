# app/api/v1/endpoints/analyze_enqueue.py
from app import auth, db, models
from app.schemas.inputs.analyze_request import AnalyzeRequest
from app.services.job_service import JobService
from app.services.reading_store import aware_birth, build_stored_reading
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analyze", tags=["analysis"])
job_service = JobService()

get_db = Depends(db.get_db)


@router.post("/enqueue")
async def analyze_enqueue(req: AnalyzeRequest, db: AsyncSession = get_db, user_id: int = Depends(auth.get_current_userid)) -> dict:
    stored = await _load_kanji(req.name_sei, req.name_mei, db)
    if stored is None:
        raise HTTPException(status_code=422, detail="康熙画数が不明な文字があるため鑑定できません")

    birth_dt = aware_birth(req.birth_date, int(req.birth_hour), req.birth_tz)
    result_birth, result_name, _prompt = build_stored_reading(birth_dt, req.sex, _strokes(req.name_sei, stored), _strokes(req.name_mei, stored))

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
    return {"job_id": job.job_id, "result_birth": result_birth, "result_name": result_name}


async def _load_kanji(name_sei: str, name_mei: str, db: AsyncSession) -> dict[str, models.Kanji] | None:
    chars = list({ch for ch in name_sei + name_mei if ch.strip()})
    stmt = select(models.Kanji).where(models.Kanji.char.in_(chars))
    kanji = await db.execute(stmt)
    stored = {row[0].char: row[0] for row in kanji.fetchall()}
    if not all(ch in stored and stored[ch].strokes_kangxi is not None for ch in chars):
        return None
    return stored


def _strokes(name: str, stored: dict[str, models.Kanji]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for ch in name:
        if not ch.strip():
            continue
        strokes = stored[ch].strokes_kangxi
        if strokes is None:
            continue
        out.append((ch, int(strokes)))
    return out


# req.name_seiとreq.name_meiに含まれる文字がKanjiテーブルに存在しない場合Falseを返す
async def validate_kanji_characters(name_sei: str, name_mei: str, db: AsyncSession) -> bool:
    return await _load_kanji(name_sei, name_mei, db) is not None
