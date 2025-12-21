import json
import logging
import os
import time
from datetime import datetime
from typing import List

from app import db, models
from app.dtos.inputs.analyze_request import AnalyzeRequest
from app.dtos.outputs.analysis_out import AnalysisOut
from app.services.calc_meishiki import get_meishiki
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
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


@app.on_event("startup")
def apply_migrations():
    """Apply SQL migrations found in backend/migrations/init.sql if DB is reachable.

    This is idempotent and will be skipped if the DB is not available (useful for
    local dev where a DB may not be present).
    """
    migrations_file = os.path.join(
        os.path.dirname(__file__), "..", "migrations", "init.sql"
    )
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
            logger.warning(
                "DB not ready (attempt %d/%d): %s", attempt, max_attempts, oe
            )
            time.sleep(delay_seconds)
        except Exception as e:
            logger.error("Failed to apply migrations: %s", e)
            return

    logger.error(
        "Exceeded max attempts (%d) applying migrations; giving up.", max_attempts
    )


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

    birth_date: datetime.date = datetime.fromisoformat(req.birth_date).date()
    birth_hour: int = int(req.birth_hour)

    # 四柱推命 ー 命式の取得
    birth_dt: datetime = datetime.combine(birth_date, datetime.min.time()).replace(
        hour=birth_hour
    )
    meishiki: dict = get_meishiki(dt=birth_dt)

    # 四柱推命 ー 五行取得
    from app.services.calc_gogyo import calc_wuxing_balance

    gogyo_balance: dict[str, int] = calc_wuxing_balance(meishiki)
    """gogyo_balance: {'木': 4, '火': 2, '土': 1, '金': 1, '水': 0}"""

    # 四柱推命 ー 総合鑑定
    from app.services.calc_birth_analysis import synthesize_reading

    birth_analysis = synthesize_reading(meishiki, gogyo_balance)
    """
    birth_analysis = {
    "四柱": {
        "年柱": {
        "柱": "年柱",
        "干支": "乙卯",
        "意味": "家系・幼少期・ルーツに影響。家族の価値観や幼少期の性質を示す。",
        "まとめ": "年柱は家系・幼少期・ルーツに影響。家族の価値観や幼少期の性質を示す。。柔らかく調和的。人間関係に強い。、社交性と調和。人間関係に恵まれる。の性質が強く表れる。",
        "十干の性質": "柔らかく調和的。人間関係に強い。",
        "十二支の性質": "社交性と調和。人間関係に恵まれる。"
        },
        "日柱": {
        "柱": "日柱",
        "干支": "庚辰",
        "意味": "本人の本質・性格・結婚運を示す。人生の中心となる柱。",
        "まとめ": "日柱は本人の本質・性格・結婚運を示す。人生の中心となる柱。。意志が強く、改革精神がある。、理想が高く、創造力がある。の性質が強く表れる。",
        "十干の性質": "意志が強く、改革精神がある。",
        "十二支の性質": "理想が高く、創造力がある。"
        },
        "時柱": {
        "柱": "時柱",
        "干支": "丙卯",
        "意味": "晩年運・子供運・才能を示す。後半生のテーマが表れる。",
        "まとめ": "時柱は晩年運・子供運・才能を示す。後半生のテーマが表れる。。明るく情熱的。表現力が豊か。、社交性と調和。人間関係に恵まれる。の性質が強く表れる。",
        "十干の性質": "明るく情熱的。表現力が豊か。",
        "十二支の性質": "社交性と調和。人間関係に恵まれる。"
        },
        "月柱": {
        "柱": "月柱",
        "干支": "乙寅",
        "意味": "社会・青年期・仕事運に影響。20〜40代の運勢や社会的立場を示す。",
        "まとめ": "月柱は社会・青年期・仕事運に影響。20〜40代の運勢や社会的立場を示す。。柔らかく調和的。人間関係に強い。、行動力と勇気。リーダーシップ。の性質が強く表れる。",
        "十干の性質": "柔らかく調和的。人間関係に強い。",
        "十二支の性質": "行動力と勇気。リーダーシップ。"
        }
    },
    "総合テーマ": {
        "性格": [
        "人との縁が強く、成長意欲が高い。新しいことに挑戦する力がある。"
        ],
        "課題": [
        "考えすぎたり、逆に思考が浅くなったりする。柔軟性が不足しがち。"
        ],
        "人生の流れ": [
        "年柱は家系・幼少期・ルーツに影響。家族の価値観や幼少期の性質を示す。。柔らかく調和的。人間関係に強い。、社交性と調和。人間関係に恵まれる。の性質が強く表れる。",
        "月柱は社会・青年期・仕事運に影響。20〜40代の運勢や社会的立場を示す。。柔らかく調和的。人間関係に強い。、行動力と勇気。リーダーシップ。の性質が強く表れる。",
        "日柱は本人の本質・性格・結婚運を示す。人生の中心となる柱。。意志が強く、改革精神がある。、理想が高く、創造力がある。の性質が強く表れる。",
        "時柱は晩年運・子供運・才能を示す。後半生のテーマが表れる。。明るく情熱的。表現力が豊か。、社交性と調和。人間関係に恵まれる。の性質が強く表れる。"
        ]
    },
    "五行バランス": {
        "日主": "金",
        "相性": {
        "助ける五行": "水",
        "弱らせる五行": "木"
        },
        "課題": [
        "考えすぎたり、逆に思考が浅くなったりする。柔軟性が不足しがち。"
        ],
        "弱い五行": [
        "水"
        ],
        "強い五行": [
        "木"
        ],
        "性格傾向": [
        "人との縁が強く、成長意欲が高い。新しいことに挑戦する力がある。"
        ]
    }
    }
    """

    # 姓名判断 ー 五格取得

    # Return the dummy result structure specified in the prompt
    result = {
        "birth_analysis": {
            "meishiki": {
                "year": meishiki["年柱"],
                "month": meishiki["月柱"],
                "day": meishiki["日柱"],
                "hour": meishiki["時柱"],
                "summary": birth_analysis,
            },
            "gogyo": {
                "wood": 26,
                "fire": 15,
                "earth": 11,
                "metal": 22,
                "water": 37,
                "summary": (
                    "「木（金を切る）と火（金を溶かす）が多いため、日主の辛（金）は"
                    "試練を受けやすいが、努力で輝きを増すタイプ。人間関係や環境から刺激を受けて成長する人生。"
                ),
            },
            "summary": (
                "美意識やこだわりを持ち、周囲から「個性的」「センスがある」と見られやすい。"
                "人との縁が強く、交流や人脈が人生のテーマ。試練を通じて磨かれる運勢で、困難を乗り越えるほど輝きが増す。"
                "晩年は人間関係に恵まれ、後進を育てる立場に向く。柔軟性・流れ」を意識するとさらに良い"
            ),
        },
        "name_analysis": {
            "tenkaku": 26,
            "jinkaku": 15,
            "chikaku": 11,
            "gaikaku": 22,
            "soukaku": 37,
            "summary": "努力家で晩年安定",
        },
        "summary": (
            "全体的にバランスが良く、特に水の要素が強いです。柔軟性と流れを意識するとさらに良いでしょう。"
            "名前の五格も努力家で晩年安定しています。"
        ),
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
def list_analyses(limit: int = 50, db: Session = get_db_dependency):
    """Return recent analyses ordered by newest first."""
    with db as session:
        qs = (
            session.query(models.Analysis)
            .order_by(models.Analysis.id.desc())
            .limit(limit)
            .all()
        )
    out = []
    for a in qs:
        out.append(
            AnalysisOut(
                id=a.id,
                name=a.name,
                birth_date=a.birth_date.isoformat(),
                birth_hour=a.birth_hour,
                result_name=(
                    json.loads(a.result_name)
                    if isinstance(a.result_name, str)
                    else a.result_name
                ),
                result_birth=(
                    json.loads(a.result_birth)
                    if isinstance(a.result_birth, str)
                    else a.result_birth
                ),
                summary=a.summary,
                created_at=a.created_at.isoformat() if a.created_at else None,
            )
        )
    return out


@app.delete("/analyses/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = get_db_dependency):
    """Delete an analysis by ID."""
    with db as session:
        obj = (
            session.query(models.Analysis)
            .filter(models.Analysis.id == analysis_id)
            .first()
        )
        if not obj:
            return {"status": "not found"}
        session.delete(obj)
        session.commit()
    return {"status": "deleted"}
