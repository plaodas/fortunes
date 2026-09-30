from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app import db, models
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

SUMMARY_LIMIT = 150


def summarize_detail(text: str, limit: int = SUMMARY_LIMIT) -> str:
    """Use the first non-empty paragraph, capped at `limit` characters."""
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first[:limit]


def llm_target() -> tuple[str, str]:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    raw_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    if provider == "ollama" and not raw_model.startswith("ollama/"):
        return provider, f"ollama/{raw_model}"
    return provider, raw_model


async def process_analysis(ctx: Any, user_id: int, name_sei: str, name_mei: str, birth_date: str, birth_hour: int, birth_tz: str = "Asia/Tokyo") -> dict[str, Any]:
    """Arq worker task: perform the analysis and persist result.

    Returns a dict summary for convenience.
    """
    # birth_date(YYYY-MM-dd) + birth_hour
    birth_date_obj = date.fromisoformat(birth_date)
    # datetime 🌟タイムゾーンの扱いに注意が必要
    try:
        tz = ZoneInfo(birth_tz)
    except Exception:
        tz = ZoneInfo("Asia/Tokyo")
    birth_dt = datetime(year=birth_date_obj.year, month=birth_date_obj.month, day=birth_date_obj.day, hour=birth_hour, tzinfo=tz)

    meishiki = get_meishiki(dt=birth_dt)
    gogyo_balance = calc_wuxing_balance(meishiki)
    birth_analysis = synthesize_reading(meishiki, gogyo_balance)

    # fetch kanji strokes using async session
    async with db.SessionLocal() as session:
        try:

            async def _get_strokes(chars: list[str]):
                out = []
                for ch in chars:
                    if not ch or not ch.strip():
                        continue
                    c = ch[0]
                    k = await session.get(models.Kanji, c)
                    out.append((ch, int(k.strokes_min) if (k and k.strokes_min is not None) else 0))
                return out

            strokes_sei = await _get_strokes(list(name_sei))
            strokes_mei = await _get_strokes(list(name_mei))

            gogaku = get_gogaku(strokes_sei, strokes_mei)

            ctx_data = birth_analysis | gogaku
            prompts_detail_user = render_life_analysis(ctx_data, TEMPLATE_DETAIL_USER)

            provider, model = llm_target()
            adapter = litellm_adapter.LiteLlmAdapter(provider=provider, model=model)
            llm_response_detail = await adapter.make_analysis(user_id=user_id, system_prompt=TEMPLATE_DETAIL_SYSTEM, user_prompt=prompts_detail_user)
            detail_text = llm_response_detail.response_text if llm_response_detail else ""
            summary_text = summarize_detail(detail_text) if detail_text else None

            birth_analysis = {
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
            }
            name_analysis = {
                "tenkaku": gogaku["五格"]["天格"]["吉凶ポイント"],
                "jinkaku": gogaku["五格"]["人格"]["吉凶ポイント"],
                "chikaku": gogaku["五格"]["地格"]["吉凶ポイント"],
                "gaikaku": gogaku["五格"]["外格"]["吉凶ポイント"],
                "soukaku": gogaku["五格"]["総格"]["吉凶ポイント"],
                "summary": None,
            }

            # persist Analysis
            obj = models.Analysis(
                user_id=user_id,
                name=name_sei + " " + name_mei,
                birth_datetime=birth_dt,
                birth_tz=birth_tz,
                result_birth=birth_analysis,
                result_name=name_analysis,
                summary=summary_text,
                detail=detail_text or None,
            )
            session.add(obj)
            await session.commit()

            ret = {"id": obj.id, "name": obj.name}

            # Arq のワーカーは「1 ジョブ＝1 タスク」create_task() しても同じイベントループ内で動くだけなので結局同じプロセス・同じワーカーで実行される
            # TODO: LOGは再エンキューする
            async with db.SessionLocal() as session_log:
                try:
                    session_log.add(llm_response_detail)
                    await session_log.commit()
                except Exception:
                    await session_log.rollback()

                finally:
                    await session_log.close()

        except Exception:
            await session.rollback()
            raise

        finally:
            await session.close()

    return ret
