import json
import logging
from datetime import datetime
from typing import List

from app import db, models
from app.dtos.inputs.analyze_request import AnalyzeRequest
from app.dtos.outputs.analysis_out import AnalysisOut
from app.services.calc_birth_analysis import synthesize_reading
from app.services.calc_gogyo import calc_wuxing_balance
from app.services.calc_meishiki import get_meishiki
from app.services.calc_name_analysis import get_gogaku, get_kanji
from app.services.constants import KAKUSUU_FORTUNE
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

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

    # 姓名判断 ー 五格取得
    # 名前の各漢字の画数をDBから取得
    with db.SessionLocal() as session:
        # nameの各文字について画数を取得
        strokes_sei: list[tuple[str, int]] = [get_kanji(session, ch) for ch in req.name_sei if ch.strip()]
        strokes_mei: list[tuple[str, int]] = [get_kanji(session, ch) for ch in req.name_mei if ch.strip()]

    gogaku = get_gogaku(strokes_sei, strokes_mei)

    # 四柱推命と姓名判断の結果から LLMに解析を依頼
    # TODO:

    # Return the dummy result structure specified in the prompt
    result = {
        "birth_analysis": {
            "meishiki": {
                "year": meishiki.get("年柱"),
                "month": meishiki.get("月柱"),
                "day": meishiki.get("日柱"),
                "hour": meishiki.get("時柱"),
                "summary": birth_analysis.get("summary"),
            },
            "gogyo": {
                "wood": gogyo_balance.get("木", 0),
                "fire": gogyo_balance.get("火", 0),
                "earth": gogyo_balance.get("土", 0),
                "metal": gogyo_balance.get("金", 0),
                "water": gogyo_balance.get("水", 0),
            },
            "summary": None,
        },
        "name_analysis": {
            "tenkaku": {"value": gogaku.get("天格"), "fortune": KAKUSUU_FORTUNE.get(gogaku.get("天格"))},  # 天格は吉凶関係ない
            "jinkaku": {"value": gogaku.get("人格"), "fortune": KAKUSUU_FORTUNE.get(gogaku.get("人格"))},
            "chikaku": {"value": gogaku.get("地格"), "fortune": KAKUSUU_FORTUNE.get(gogaku.get("地格"))},
            "gaikaku": {"value": gogaku.get("外格"), "fortune": KAKUSUU_FORTUNE.get(gogaku.get("外格"))},
            "soukaku": {"value": gogaku.get("総格"), "fortune": KAKUSUU_FORTUNE.get(gogaku.get("総格"))},
            "summary": None,
        },
        "summary": "",
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
        )
        with db.SessionLocal() as session:
            session.add(db_obj)
            session.commit()
    except Exception as e:
        logger.warning("Could not persist analysis to DB: %s", e)

    return {"input": req.dict(), "result": result}


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
