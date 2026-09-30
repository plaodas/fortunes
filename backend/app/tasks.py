from __future__ import annotations

import os
import re
from datetime import date
from typing import Any

from app import db, models
from app.services import litellm_adapter
from app.services.make_story import render_life_analysis
from app.services.prompts.template_life_analysis import (
    TEMPLATE_DETAIL_SYSTEM,
    TEMPLATE_DETAIL_USER,
)
from app.services.reading_store import aware_birth, build_stored_reading

SUMMARY_LIMIT = 150
_MARKUP_LINE = re.compile(r"^(?:#{1,6}\s*\S.*|([-*_])\1{2,})$")


def summarize_detail(text: str, limit: int = SUMMARY_LIMIT) -> str:
    """Use the first non-empty paragraph, capped at `limit` characters.

    Markdown headings and horizontal rules are skipped so a title line is not stored as the summary.
    """
    for line in text.splitlines():
        line = line.strip()
        if not line or _MARKUP_LINE.match(line):
            continue
        return line[:limit]
    return ""


def llm_target() -> tuple[str, str]:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    raw_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    if provider == "ollama" and not raw_model.startswith("ollama/"):
        return provider, f"ollama/{raw_model}"
    return provider, raw_model


async def process_analysis(ctx: Any, user_id: int, name_sei: str, name_mei: str, birth_date: str, birth_hour: int, sex: str, birth_tz: str = "Asia/Tokyo") -> dict[str, Any]:
    """Arq worker task: perform the analysis and persist result.

    Returns a dict summary for convenience.
    """
    birth_dt = aware_birth(date.fromisoformat(birth_date), birth_hour, birth_tz)

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
                    if k is None or k.strokes_kangxi is None:
                        raise ValueError(f"康熙画数がありません: {c}")
                    out.append((ch, int(k.strokes_kangxi)))
                return out

            strokes_sei = await _get_strokes(list(name_sei))
            strokes_mei = await _get_strokes(list(name_mei))

            result_birth, result_name, ctx_data = build_stored_reading(birth_dt, sex, strokes_sei, strokes_mei)
            prompts_detail_user = render_life_analysis(ctx_data, TEMPLATE_DETAIL_USER)

            provider, model = llm_target()
            adapter = litellm_adapter.LiteLlmAdapter(provider=provider, model=model)
            llm_response_detail = await adapter.make_analysis(user_id=user_id, system_prompt=TEMPLATE_DETAIL_SYSTEM, user_prompt=prompts_detail_user)
            detail_text = llm_response_detail.response_text if llm_response_detail else ""
            summary_text = summarize_detail(detail_text) if detail_text else None

            obj = models.Analysis(
                user_id=user_id,
                name=name_sei + " " + name_mei,
                birth_datetime=birth_dt,
                birth_tz=birth_tz,
                result_birth=result_birth,
                result_name=result_name,
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
