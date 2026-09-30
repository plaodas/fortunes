"""命式・五行・五格を、保存用の辞書にまとめる。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.services.calc_birth_analysis import synthesize_reading
from app.services.calc_gogyo import calc_wuxing_balance
from app.services.calc_meishiki import get_meishiki
from app.services.calc_name_analysis import get_gogaku
from app.services.calc_stars import calc_daiun


def aware_birth(birth_date: date, birth_hour: int, birth_tz: str) -> datetime:
    try:
        tz = ZoneInfo(birth_tz)
    except Exception:
        tz = ZoneInfo("Asia/Tokyo")
    return datetime(birth_date.year, birth_date.month, birth_date.day, birth_hour, tzinfo=tz)


def build_stored_reading(birth_dt: datetime, sex: str, strokes_sei: list[tuple[str, int]], strokes_mei: list[tuple[str, int]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """保存する result_birth / result_name と、プロンプト用の日本語コンテキストを返す。"""
    meishiki = get_meishiki(dt=birth_dt)
    gogyo_balance = calc_wuxing_balance(meishiki)
    daiun = calc_daiun(birth_dt, sex, meishiki["年柱"][0], meishiki["月柱"], meishiki["日柱"][0])
    synthesized = synthesize_reading(meishiki, gogyo_balance, daiun=daiun)
    gogaku = get_gogaku(strokes_sei, strokes_mei)
    pillars = synthesized["四柱"]
    result_birth = {
        "meishiki": {
            "year": meishiki.get("年柱"),
            "month": meishiki.get("月柱"),
            "day": meishiki.get("日柱"),
            "hour": meishiki.get("時柱"),
            "summary": "",
            "strength": synthesized["身強身弱"],
            "sex": sex,
            "pillars": {
                key: {
                    "kanshi": pillars[name]["干支"],
                    "tsuhen": pillars[name]["通変星"],
                    "juniun": pillars[name]["十二運"],
                }
                for key, name in (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "時柱"))
            },
            "daiun": [{"start": row["開始"], "kanshi": row["干支"], "tsuhen": row["通変星"]} for row in synthesized["大運"]],
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
    result_name = {
        "tenkaku": gogaku["五格"]["天格"]["吉凶ポイント"],
        "jinkaku": gogaku["五格"]["人格"]["吉凶ポイント"],
        "chikaku": gogaku["五格"]["地格"]["吉凶ポイント"],
        "gaikaku": gogaku["五格"]["外格"]["吉凶ポイント"],
        "soukaku": gogaku["五格"]["総格"]["吉凶ポイント"],
        "summary": None,
    }
    return result_birth, result_name, synthesized | gogaku
