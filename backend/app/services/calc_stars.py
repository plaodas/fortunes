"""通変星、十二運、身強身弱、大運。"""

from __future__ import annotations

from datetime import datetime

from app.services.constants import (
    CHANGSHENG_BRANCH,
    HIDDEN_STEMS,
    JUNISHI,
    SUPPORTING_GODS,
    TENKAN,
    TWELVE_STAGES,
)
from app.services.solar_terms import neighboring_jie

_PILLAR_NAMES = ("年柱", "月柱", "日柱", "時柱")
_KANSHI = [TENKAN[i % 10] + JUNISHI[i % 12] for i in range(60)]


def ten_god(day_stem: str, other_stem: str) -> str:
    """日干から見た通変星。同じ陰陽が比肩・食神・偏財・七殺・偏印。"""
    day_i = TENKAN.index(day_stem)
    other_i = TENKAN.index(other_stem)
    relation = (other_i // 2 - day_i // 2) % 5
    same_polarity = (day_i % 2) == (other_i % 2)
    table = {
        0: ("比肩", "劫財"),
        1: ("食神", "傷官"),
        2: ("偏財", "正財"),
        3: ("七殺", "正官"),
        4: ("偏印", "正印"),
    }
    return table[relation][0 if same_polarity else 1]


def twelve_stage(day_stem: str, branch: str) -> str:
    start = JUNISHI.index(CHANGSHENG_BRANCH[day_stem])
    branch_i = JUNISHI.index(branch)
    if TENKAN.index(day_stem) % 2 == 0:
        index = (branch_i - start) % 12
    else:
        index = (start - branch_i) % 12
    return TWELVE_STAGES[index]


def hidden_stem_names(branch: str) -> list[str]:
    return [stem for stem, _is_main in HIDDEN_STEMS[branch]]


def body_strength(meishiki: dict[str, str]) -> str:
    """印・比劫は +1、食傷・財・官殺は -1。月支の本気だけ 2 倍。"""
    day_stem = meishiki["日柱"][0]
    score = 0
    for name in _PILLAR_NAMES:
        pillar = meishiki[name]
        stems: list[tuple[str, int]] = [(pillar[0], 1)]
        for stem, is_main in HIDDEN_STEMS[pillar[1]]:
            weight = 2 if name == "月柱" and is_main else 1
            stems.append((stem, weight))
        for stem, weight in stems:
            sign = 1 if ten_god(day_stem, stem) in SUPPORTING_GODS else -1
            score += sign * weight
    if score > 0:
        return "身強"
    if score < 0:
        return "身弱"
    return "中和"


def _shift(pillar: str, steps: int) -> str:
    return _KANSHI[(_KANSHI.index(pillar) + steps) % 60]


def _start_age(birth: datetime, boundary: datetime) -> tuple[int, int]:
    days = abs((boundary - birth).total_seconds()) / 86400
    years = int(days // 3)
    months = int((days % 3) * 4)
    years += months // 12
    months %= 12
    return years, months


def is_forward(year_stem: str, sex: str) -> bool:
    """陽年の男と陰年の女は順行。"""
    yang_year = TENKAN.index(year_stem) % 2 == 0
    male = sex == "male"
    return yang_year == male


def calc_daiun(birth: datetime, sex: str, year_stem: str, month_pillar: str, day_stem: str, periods: int = 8) -> list[dict[str, str]]:
    forward = is_forward(year_stem, sex)
    years, months = _start_age(birth, neighboring_jie(birth, forward=forward))
    step = 1 if forward else -1
    rows = []
    for index in range(1, periods + 1):
        kanshi = _shift(month_pillar, step * index)
        rows.append(
            {
                "開始": f"{years + (index - 1) * 10}歳{months}ヶ月",
                "干支": kanshi,
                "通変星": ten_god(day_stem, kanshi[0]),
            }
        )
    return rows
