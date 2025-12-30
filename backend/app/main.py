import inspect
import json
import logging
from datetime import datetime
from typing import List

from app import db, models
from app.dtos.inputs.analyze_request import AnalyzeRequest
from app.dtos.outputs.analysis_out import AnalysisOut

# adapter for provider switching
from app.services import litellm_adapter
from app.services.calc_birth_analysis import synthesize_reading
from app.services.calc_gogyo import calc_wuxing_balance
from app.services.calc_meishiki import get_meishiki
from app.services.calc_name_analysis import get_gogaku
from app.services.make_story import render_life_analysis
from app.services.prompts.template_life_analysis import (
    TEMPLATE_DETAIL_SYSTEM,
    TEMPLATE_DETAIL_USER,
)
from app.services.prompts.template_life_analysis_summary import (
    TEMPLATE_SUMMARY_SYSTEM,
    TEMPLATE_SUMMARY_USER,
)
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
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
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest, db_sess: AsyncSession = get_db_dependency):
    """Perform fortune analysis based on name(sei and mei) and birth date/hour.
    Returns a dummy result for now.
    """
    # 命式と五行・五格の解析
    birth_date: datetime.date = datetime.fromisoformat(req.birth_date).date()
    birth_hour: int = int(req.birth_hour)

    # 四柱推命 ー 命式の取得
    birth_dt: datetime = datetime.combine(birth_date, datetime.min.time()).replace(hour=birth_hour)
    meishiki: dict = get_meishiki(dt=birth_dt)

    # 四柱推命 ー 五行取得
    gogyo_balance: dict[str, int] = calc_wuxing_balance(meishiki)
    """gogyo_balance: {'木': 4, '火': 2, '土': 1, '金': 1, '水': 0}"""

    # 四柱推命 ー 総合鑑定
    birth_analysis = synthesize_reading(meishiki, gogyo_balance)

    logger.debug("🌟Finished birth analysis...")

    # 姓名判断 ー 五格取得
    # 名前の各漢字の画数をDBから取得（AsyncSessionで取得）
    async def _get_strokes(session: AsyncSession, chars: list[str]) -> list[tuple[str, int]]:
        out: list[tuple[str, int]] = []
        for ch in chars:
            if not ch or not ch.strip():
                continue
            c = ch[0]
            k = await session.get(models.Kanji, c)
            if not k or k.strokes_min is None:
                out.append((ch, 0))
            else:
                out.append((ch, int(k.strokes_min)))
        return out

    strokes_sei: list[tuple[str, int]] = await _get_strokes(db_sess, req.name_sei)
    strokes_mei: list[tuple[str, int]] = await _get_strokes(db_sess, req.name_mei)

    logger.debug("🌟Finished name analysis...")

    gogaku = get_gogaku(strokes_sei, strokes_mei)
    """
    gogaku: {"五格": {
        '天格': {"値":10, "吉凶":"大凶", "桃源":{"長文":"桃源の風があなたを包み、道は光に満ちて開けていく。"}},
        '人格': {"値":15, "吉凶":"大吉", "桃源":{"長文":"桃源の風があなたを包み、道は光に満ちて開けていく。"}},
        '地格': {"値":20, "吉凶":"吉", "桃源":{"長文":"桃源の風があなたを包み、道は光に満ちて開けていく。"}},
        '外格': {"値":15, "吉凶":"中吉", "桃源":{"長文":"桃源の風があなたを包み、道は光に満ちて開けていく。"}},
        '総格': {"値":30, "吉凶":"小吉", "桃源":{"長文":"桃源の風があなたを包み、道は光に満ちて開けていく。"}}
    }}
    """

    # 四柱推命と姓名判断の結果から LLM解析依頼用のプロンプトを生成
    ctx: dict = birth_analysis | gogaku
    prompts_detail_user = render_life_analysis(ctx, TEMPLATE_DETAIL_USER)
    prompts_summary_user = render_life_analysis(ctx, TEMPLATE_SUMMARY_USER)

    logger.debug(f"🌟Start make reports {prompts_detail_user[:60]}...")

    async def _maybe_await(value):
        try:
            while inspect.isawaitable(value):
                value = await value
        except Exception:
            # if awaiting fails, just return the original value to let outer try/except handle it
            return value
        return value

    try:
        # 四柱推命と姓名判断の結果から LLM解析依頼用のプロンプトを生成
        report_detail = await _maybe_await(
            litellm_adapter.make_analysis_detail(
                TEMPLATE_DETAIL_SYSTEM,
                prompts_detail_user,
            )
        )
        logger.debug(f"🌟Received detail response: {str(report_detail)[:60]}...")

        report_summary = await _maybe_await(
            litellm_adapter.make_analysis_summary(
                TEMPLATE_SUMMARY_SYSTEM,
                prompts_summary_user,
            )
        )
        logger.debug(f"🌟Received summary response: {str(report_summary)[:60]}...")

    except Exception:
        return {"error": "しばらく経ってから再度お試しください。"}

    # Return the dummy result structure specified in the prompt
    result = {
        "birth_analysis": {
            "meishiki": {
                "year": meishiki.get("年柱"),
                "month": meishiki.get("月柱"),
                "day": meishiki.get("日柱"),
                "hour": meishiki.get("時柱"),
                "summary": "",
            },
            "gogyo": {
                "wood": gogyo_balance.get("木", 0),
                "fire": gogyo_balance.get("火", 0),
                "earth": gogyo_balance.get("土", 0),
                "metal": gogyo_balance.get("金", 0),
                "water": gogyo_balance.get("水", 0),
            },
            "summary": "",
        },
        "name_analysis": {
            "tenkaku": gogaku.get("五格").get("天格").get("吉凶ポイント"),
            "jinkaku": gogaku.get("五格").get("人格").get("吉凶ポイント"),
            "chikaku": gogaku.get("五格").get("地格").get("吉凶ポイント"),
            "gaikaku": gogaku.get("五格").get("外格").get("吉凶ポイント"),
            "soukaku": gogaku.get("五格").get("総格").get("吉凶ポイント"),
            "summary": None,
        },
        "detail": report_detail,
        "summary": report_summary,
    }

    # Persist to DB if possible (AsyncSession)
    try:
        db_obj = models.Analysis(
            name=req.name_sei + " " + req.name_mei,
            birth_date=birth_date,
            birth_hour=birth_hour,
            result_birth=result["birth_analysis"],
            result_name=result["name_analysis"],
            summary=result["summary"],
            detail=result["detail"],
        )
        db_sess.add(db_obj)
        await db_sess.commit()
    except Exception as e:
        logger.warning("Could not persist analysis to DB: %s", e)

    return {"input": req.model_dump(), "result": result}


@app.get("/analyses", response_model=List[AnalysisOut])
async def list_analyses(limit: int = 50, db: AsyncSession = get_db_dependency):
    """Return recent analyses ordered by newest first."""
    stmt = select(models.Analysis).order_by(models.Analysis.id.desc()).limit(limit)
    res = await db.execute(stmt)
    qs = res.scalars().all()
    out = []
    for a in qs:
        out.append(
            AnalysisOut(
                id=a.id,
                name=a.name,
                birth_date=a.birth_date.isoformat(),
                birth_hour=a.birth_hour,
                result_name=(json.loads(a.result_name) if isinstance(a.result_name, str) else a.result_name),
                result_birth=(json.loads(a.result_birth) if isinstance(a.result_birth, str) else a.result_birth),
                summary=a.summary,
                detail=a.detail,
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
