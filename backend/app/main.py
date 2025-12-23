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
from app.services.calc_name_analysis import get_gogaku, get_kanji
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
from sqlalchemy.orm import Session

# Use a module-level Depends wrapper to satisfy ruff B008
get_db_dependency = Depends(db.get_db)

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

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
def analyze(req: AnalyzeRequest):
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
    # 名前の各漢字の画数をDBから取得
    with db.SessionLocal() as session:
        # nameの各文字について画数を取得
        strokes_sei: list[tuple[str, int]] = [get_kanji(session, ch) for ch in req.name_sei if ch.strip()]
        strokes_mei: list[tuple[str, int]] = [get_kanji(session, ch) for ch in req.name_mei if ch.strip()]

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

    try:
        report_detail = litellm_adapter.make_analysis_detail(
            system_prompt=TEMPLATE_DETAIL_SYSTEM,
            user_prompt=prompts_detail_user,
        )
        # 結果の表示 (OpenAI互換のレスポンス形式で返ってきます)
        logger.debug(f"🌟Received detail response: {report_detail[:60]}...")

        report_summary = litellm_adapter.make_analysis_summary(
            system_prompt=TEMPLATE_SUMMARY_SYSTEM,
            user_prompt=prompts_summary_user,
        )
        # 結果の表示 (OpenAI互換のレスポンス形式で返ってきます)
        logger.debug(f"🌟Received summary response: {report_summary[:60]}...")

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
            "tenkaku": gogaku.get("五格").get("天格").get("値"),
            "jinkaku": gogaku.get("五格").get("人格").get("値"),
            "chikaku": gogaku.get("五格").get("地格").get("値"),
            "gaikaku": gogaku.get("五格").get("外格").get("値"),
            "soukaku": gogaku.get("五格").get("総格").get("値"),
            "summary": None,
        },
        "detail": report_detail,
        "summary": report_summary,
    }

    # Persist to DB if possible
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
        with db.SessionLocal() as session:
            session.add(db_obj)
            session.commit()
    except Exception as e:
        logger.warning("Could not persist analysis to DB: %s", e)

    return {"input": req.model_dump(), "result": result}


@app.get("/analyses", response_model=List[AnalysisOut])
def list_analyses(limit: int = 50, db: Session = get_db_dependency):
    """Return recent analyses ordered by newest first."""
    with db as session:
        qs = session.query(models.Analysis).order_by(models.Analysis.id.desc()).limit(limit).all()
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
def delete_analysis(analysis_id: int, db: Session = get_db_dependency):
    """Delete an analysis by ID."""
    with db as session:
        obj = session.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
        if not obj:
            return {"status": "not found"}
        session.delete(obj)
        session.commit()
    return {"status": "deleted"}
