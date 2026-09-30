"""十二節の時刻。

月柱に使うのは中気ではなく節（小寒・立春・啓蟄・清明・立夏・芒種・小暑・立秋・白露・寒露・立冬・大雪）。
太陽黄経は Meeus『Astronomical Algorithms』の略算。時刻は UTC。
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from functools import lru_cache

# (黄経, おおよその月, 日, その節から始まる月支)
_JIE: tuple[tuple[int, int, int, str], ...] = (
    (285, 1, 5, "丑"),  # 小寒
    (315, 2, 4, "寅"),  # 立春
    (345, 3, 6, "卯"),  # 啓蟄
    (15, 4, 5, "辰"),  # 清明
    (45, 5, 6, "巳"),  # 立夏
    (75, 6, 6, "午"),  # 芒種
    (105, 7, 7, "未"),  # 小暑
    (135, 8, 8, "申"),  # 立秋
    (165, 9, 8, "酉"),  # 白露
    (195, 10, 8, "戌"),  # 寒露
    (225, 11, 7, "亥"),  # 立冬
    (255, 12, 7, "子"),  # 大雪
)


def _julian_day(dt: datetime) -> float:
    dt = dt.astimezone(timezone.utc)
    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600 + dt.microsecond / 3_600_000_000) / 24
    if month <= 2:
        year -= 1
        month += 12
    century = year // 100
    gregorian = 2 - century + century // 4
    return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + gregorian - 1524.5


def _sun_longitude(jd: float) -> float:
    """視黄経（度）。"""
    t = (jd - 2451545.0) / 36525.0
    mean_long = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    mean_anom = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    center = (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mean_anom) + (0.019993 - 0.000101 * t) * math.sin(2 * mean_anom) + 0.000289 * math.sin(3 * mean_anom)
    omega = math.radians(125.04 - 1934.136 * t)
    return (mean_long + center - 0.00569 - 0.00478 * math.sin(omega)) % 360


def _angle_diff(longitude: float, target: float) -> float:
    return (longitude - target + 180) % 360 - 180


def _term_instant(year: int, longitude: int, month: int, day: int) -> datetime:
    start = datetime(year, month, day, tzinfo=timezone.utc) - timedelta(days=20)
    end = start + timedelta(days=40)
    for _ in range(60):
        mid = start + (end - start) / 2
        if _angle_diff(_sun_longitude(_julian_day(mid)), longitude) < 0:
            start = mid
        else:
            end = mid
    return end


@lru_cache(maxsize=128)
def jie_instants(year: int) -> tuple[tuple[datetime, str], ...]:
    """その西暦年に起きる十二節を時刻順で返す。各要素は (UTC時刻, 月支)。"""
    return tuple((_term_instant(year, lon, month, day), branch) for lon, month, day, branch in _JIE)


def lichun(year: int) -> datetime:
    """立春（寅月の開始）の UTC 時刻。"""
    for instant, branch in jie_instants(year):
        if branch == "寅":
            return instant
    raise RuntimeError("立春が見つからない")


def month_branch(dt: datetime) -> str:
    """dt 時点の月支。節の瞬間から次の節の前まで。"""
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    instants: list[tuple[datetime, str]] = []
    for year in (dt.year - 1, dt.year, dt.year + 1):
        instants.extend(jie_instants(year))
    past = [item for item in instants if item[0] <= dt]
    if not past:
        raise RuntimeError("節入りが見つからない")
    return max(past, key=lambda item: item[0])[1]


def neighboring_jie(dt: datetime, forward: bool) -> datetime:
    """順行なら次の節、逆行なら直前の節（同時刻を含む）。"""
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    instants = [instant for year in (dt.year - 1, dt.year, dt.year + 1) for instant, _branch in jie_instants(year)]
    if forward:
        upcoming = [instant for instant in instants if instant > dt]
        if not upcoming:
            raise RuntimeError("次の節が見つからない")
        return min(upcoming)
    passed = [instant for instant in instants if instant <= dt]
    if not passed:
        raise RuntimeError("前の節が見つからない")
    return max(passed)
