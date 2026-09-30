"""四柱推命の命式（年柱・月柱・日柱・時柱）。

年柱・月柱は節入りで切る。月干は五虎遁（甲・己の年は寅月が丙）。
日柱は 2024-01-01 が甲子になる基準（国立天文台の暦象年表）を使う。
23時を過ぎても日柱は暦日のまま（子初換日は使わない）。
"""

from datetime import date, datetime

from .constants import HOUR_STEM_TABLE, JUNISHI, TENKAN
from .solar_terms import lichun, month_branch

# 甲子を基準にした60干支
_KANSHI = [TENKAN[i % 10] + JUNISHI[i % 12] for i in range(60)]
# 寅月を 1 とする月支
_MONTH_BRANCHES = "寅卯辰巳午未申酉戌亥子丑"
# 国立天文台の暦象年表で令和6年1月1日は甲子。そこから逆算した甲子日。
_DAY_BASE = date(1984, 3, 31)


def _year_number(dt: datetime) -> int:
    """立春で切り替わる年。立春前はその西暦の前年。"""
    if dt < lichun(dt.year):
        return dt.year - 1
    return dt.year


def _kanshi_from_offset(offset: int) -> str:
    return _KANSHI[offset % 60]


def _get_year_pillar(dt: datetime) -> str:
    """1984年（立春基準）を甲子年とする。"""
    return _kanshi_from_offset(_year_number(dt) - 1984)


def _month_stem(year_stem: str, month_index: int) -> str:
    """五虎遁。month_index は寅月を 1 とする。"""
    start = (TENKAN.index(year_stem) % 5) * 2 + 2
    return TENKAN[(start + month_index - 1) % 10]


def _get_month_pillar(dt: datetime, year_pillar: str) -> str:
    branch = month_branch(dt)
    month_index = _MONTH_BRANCHES.index(branch) + 1
    return _month_stem(year_pillar[0], month_index) + branch


def _get_day_pillar(dt: datetime) -> str:
    """その暦日の干支。タイムゾーン付きならその地域の日付を使う。"""
    idx = (dt.date() - _DAY_BASE).days % 60
    return _KANSHI[idx]


# 5. 時柱の計算（時刻＋日干から求める）
# 四柱推命の時柱は
# - 時刻 → 地支（2時間ごと）
# - 日干＋時支 → 時干
# というルールです。
def _get_hour_branch(hour: int) -> str:
    """時刻（0〜23）から時支を求める。23:00〜0:59 が子、1:00〜2:59 が丑。"""
    # 23時は子とみなす
    if hour == 23:
        idx = 0
    else:
        idx = ((hour + 1) // 2) % 12
    return JUNISHI[idx]


def _get_hour_pillar(dt: datetime, day_pillar: str) -> str:
    """
    時柱を求める
    ・時支：時刻から算出
    ・時干：日干＋時支の位置からテーブルで取得
    """
    h = dt.hour
    branch = _get_hour_branch(h)
    day_stem = day_pillar[0]

    # 子〜亥を 0〜11 に対応
    b_idx = JUNISHI.index(branch)
    stem = HOUR_STEM_TABLE[day_stem][b_idx]

    return stem + branch


# 6. 命式をまとめて計算する関数
# ここまでを1つにまとめます。
def get_meishiki(dt: datetime) -> dict[str, str]:
    """タイムゾーン付きの日時から年柱・月柱・日柱・時柱を返す。"""
    year_p = _get_year_pillar(dt)
    month_p = _get_month_pillar(dt, year_p)
    day_p = _get_day_pillar(dt)
    hour_p = _get_hour_pillar(dt, day_p)

    return {
        "年柱": year_p,
        "月柱": month_p,
        "日柱": day_p,
        "時柱": hour_p,
    }
