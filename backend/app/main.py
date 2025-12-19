from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
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


@app.on_event("startup")
def apply_migrations():
    """Apply SQL migrations found in backend/migrations/init.sql if DB is reachable.

    This is idempotent and will be skipped if the DB is not available (useful for
    local dev where a DB may not be present).
    """
    migrations_file = os.path.join(os.path.dirname(__file__), "..", "migrations", "init.sql")
    try:
        if os.path.exists(migrations_file):
            with open(migrations_file, "r", encoding="utf-8") as f:
                sql = f.read()
            # Try to execute migration SQL using SQLAlchemy engine
            with db.engine.begin() as conn:
                conn.exec_driver_sql(sql)
            logger.info("Applied migrations from %s", migrations_file)
        else:
            logger.info("No migrations file found at %s", migrations_file)
    except Exception as e:
        # If DB isn't available yet or SQL fails, just log and continue.
        logger.warning("Could not apply migrations: %s", e)


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
