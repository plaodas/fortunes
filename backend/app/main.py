from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import time
from typing import List
from sqlalchemy.orm import Session
from . import db, models
from datetime import datetime
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
    # Return the dummy result structure specified in the prompt
    result = {
        "year": "乙卯",
        "month": "戊寅",
        "day": "辛巳",
        "hour": "乙卯",
        "birthAnalysis": {
            "wood": 26,
            "fire": 15,
            "earth": 11,
            "metal": 22,
            "water": 37,
            "summary": "「柔軟性・流れ」を意識するとさらに良い",
        },
        "nameAnalysis": {
            "tenkaku": 26,
            "jinkaku": 15,
            "chikaku": 11,
            "gaikaku": 22,
            "soukaku": 37,
            "summary": "努力家で晩年安定",
        },
    }

    # Persist to DB if possible
    try:
        db_obj = models.Analysis(
            name=req.name,
            birth_date=datetime.fromisoformat(req.birth_date).date(),
            birth_hour=req.birth_hour,
            result=result,
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
                result_name=a.result_name,
                result_birth=a.result_birth,
                created_at=a.created_at.isoformat() if a.created_at else None,
            )
        )
    return out
