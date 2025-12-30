from __future__ import annotations

from typing import Any

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
from app.services.prompts.template_life_analysis_summary import (
    TEMPLATE_SUMMARY_SYSTEM,
    TEMPLATE_SUMMARY_USER,
)


async def process_analysis(ctx: Any, name_sei: str, name_mei: str, birth_date: str, birth_hour: int) -> dict:
    """Arq worker task: perform the analysis and persist result.

    Returns a dict summary for convenience.
    """
    # build datetime and run sync CPU-bound parts
    birth_date_obj = __import__("datetime").datetime.fromisoformat(birth_date).date()
    birth_dt = __import__("datetime").datetime.combine(birth_date_obj, __import__("datetime").datetime.min.time()).replace(hour=birth_hour)

    meishiki = get_meishiki(dt=birth_dt)
    gogyo_balance = calc_wuxing_balance(meishiki)
    birth_analysis = synthesize_reading(meishiki, gogyo_balance)

    # fetch kanji strokes using async session
    async with db.SessionLocal() as session:

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
        prompts_summary_user = render_life_analysis(ctx_data, TEMPLATE_SUMMARY_USER)

        # Call LLMs (async)
        report_detail = await litellm_adapter.make_analysis_detail(TEMPLATE_DETAIL_SYSTEM, prompts_detail_user)
        report_summary = await litellm_adapter.make_analysis_summary(TEMPLATE_SUMMARY_SYSTEM, prompts_summary_user)

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
            "tenkaku": gogaku.get("五格").get("天格").get("吉凶ポイント"),
            "jinkaku": gogaku.get("五格").get("人格").get("吉凶ポイント"),
            "chikaku": gogaku.get("五格").get("地格").get("吉凶ポイント"),
            "gaikaku": gogaku.get("五格").get("外格").get("吉凶ポイント"),
            "soukaku": gogaku.get("五格").get("総格").get("吉凶ポイント"),
            "summary": None,
        }

        # persist Analysis
        obj = models.Analysis(
            name=name_sei + " " + name_mei,
            birth_date=birth_date_obj,
            birth_hour=birth_hour,
            result_birth=birth_analysis,
            result_name=name_analysis,
            summary=report_summary,
            detail=report_detail,
        )
        session.add(obj)
        await session.commit()

        return {"id": obj.id, "name": obj.name}
