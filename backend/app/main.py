from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import time
from typing import List
from sqlalchemy.orm import Session

from .entities.birth_analytics import Meishiki
from .services.calc_meishiki import get_meishiki
from . import db, models
from datetime import date, datetime
import json
import os
import logging

logger = logging.getLogger("uvicorn")

app = FastAPI(title="Fortunes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    name: str
    birth_date: str  # YYYY-MM-DD
    birth_hour: int  # 0-23


class AnalysisOut(BaseModel):
    id: int
    name: str
    birth_date: str
    birth_hour: int
    result_birth: dict
    result_name: dict
    created_at: str | None = None


@app.on_event("startup")
def apply_migrations():
    """Apply SQL migrations found in backend/migrations/init.sql if DB is reachable.

    This is idempotent and will be skipped if the DB is not available (useful for
    local dev where a DB may not be present).
    """
    migrations_file = os.path.join(os.path.dirname(__file__), "..", "migrations", "init.sql")
    if not os.path.exists(migrations_file):
        logger.info("No migrations file found at %s", migrations_file)
        return

    with open(migrations_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # Retry loop: wait for DB to become available before applying migrations
    max_attempts = int(os.getenv("MIGRATE_MAX_ATTEMPTS", "15"))
    delay_seconds = float(os.getenv("MIGRATE_DELAY_SECONDS", "2"))
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        try:
            with db.engine.begin() as conn:
                conn.exec_driver_sql(sql)
            logger.info("Applied migrations from %s", migrations_file)
            return
        except OperationalError as oe:
            logger.warning("DB not ready (attempt %d/%d): %s", attempt, max_attempts, oe)
            time.sleep(delay_seconds)
        except Exception as e:
            logger.error("Failed to apply migrations: %s", e)
            return

    logger.error("Exceeded max attempts (%d) applying migrations; giving up.", max_attempts)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):

    """Perform fortune analysis based on name and birth date/hour.
    Returns a dummy result for now.
    """
    # TODO:
    # ここで命式と五行・五格の解析を行う。
    # 解析ロジックは省略し、ダミーの結果を返す

    birth_date = datetime.fromisoformat(req.birth_date).date()
    birth_hour = int(req.birth_hour)

    # 命式の取得
    birth_dt = datetime.combine(birth_date, datetime.min.time()).replace(hour=birth_hour)
    meishiki: Meishiki = get_meishiki(dt=birth_dt)

    # 五行取得




    # 五格取得



    # Return the dummy result structure specified in the prompt
    result = {
        "birth_analysis": {
            "meisiki": {
                "year": meishiki.year,
                "month": meishiki.month,
                "day": meishiki.day,
                "hour": meishiki.hour,
                "summary": "辛（金）は「宝石のような金属」で、繊細で美意識が高く、こだわりを持つタイプ。巳（火）は金を鍛える火で、試練や努力を通じて磨かれる運勢を示します",
            },
            "gogyo":{
                "wood": 26,
                "fire": 15,
                "earth": 11,
                "metal": 22,
                "water": 37,
                "summary": "「木（金を切る）と火（金を溶かす）が多いため、日主の辛（金）は試練を受けやすいが、努力で輝きを増すタイプ。人間関係や環境から刺激を受けて成長する人生。",
            },
            "summary": "美意識やこだわりを持ち、周囲から「個性的」「センスがある」と見られやすい。人との縁が強く、交流や人脈が人生のテーマ。試練を通じて磨かれる運勢で、困難を乗り越えるほど輝きが増す。晩年は人間関係に恵まれ、後進を育てる立場に向く。柔軟性・流れ」を意識するとさらに良い",
        },
        "name_analysis": {
            "tenkaku": 26,
            "jinkaku": 15,
            "chikaku": 11,
            "gaikaku": 22,
            "soukaku": 37,
            "summary": "努力家で晩年安定",
        },
        "summary": "全体的にバランスが良く、特に水の要素が強いです。柔軟性と流れを意識するとさらに良いでしょう。名前の五格も努力家で晩年安定しています。",
    }

    # Persist to DB if possible
    try:
        db_obj = models.Analysis(
            name=req.name,
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
def list_analyses(limit: int = 50, db: Session = Depends(db.get_db)):
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
                result_name=json.loads(a.result_name) if isinstance(a.result_name, str) else a.result_name,
                result_birth=json.loads(a.result_birth) if isinstance(a.result_birth, str) else a.result_birth,
                summary=a.summary,
                created_at=a.created_at.isoformat() if a.created_at else None,
            )
        )
    return out


@app.delete("/analyses/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = Depends(db.get_db)):
    """Delete an analysis by ID."""
    with db as session:
        obj = session.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
        if not obj:
            return {"status": "not found"}
        session.delete(obj)
        session.commit()
    return {"status": "deleted"}
