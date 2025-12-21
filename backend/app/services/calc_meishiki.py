"""
四柱推命の命式（年柱・月柱・日柱・時柱）を計算するロジック

ここでは「実装しやすいけど、それなりに四柱推命っぽくなる“簡易版”」を出します。
- 西暦年月日＋24時制の時刻 →
年柱・月柱・日柱・時柱（十干十二支）
※本格的にやるなら「節入り（立春など）の厳密計算」が必要ですが、ここでは
- 立春を毎年 2/4 固定
- 月干は「年干＋月番号」ルール
という、実装しやすい近似を使っています。
"""

from datetime import date, datetime

# 1. 基本データの準備
from .constants import HOUR_STEM_TABLE, JUNISHI, TENKAN

# 甲子を基準にした60干支
_KANSHI = [TENKAN[i % 10] + JUNISHI[i % 12] for i in range(60)]


# 2. 年柱の計算（簡易版：立春を2/4固定）
def _get_year_pillar(dt: datetime) -> str:
    """
    年柱を求める簡易ロジック
    ・立春を毎年 2月4日 固定とする
    """
    y = dt.year
    # 立春前なら前年として扱う
    lichun = date(y, 2, 4)
    if dt.date() < lichun:
        y -= 1

    # 参考基準：1984年を甲子年とする（実務でよく使われる近似）
    # 1984年 = 甲子
    offset = y - 1984
    idx = offset % 60
    return _KANSHI[idx]


# 3. 月柱の計算（簡易：節入り無視で“月番号”を使う）
# 四柱推命の月柱は本来「節入り」で変わりますが、
# ここではざっくり「2月＝寅月」として扱う簡易版です。
# - 寅月を1番、卯月を2番、…、丑月を12番として
# 月干＝年干の番号＋月番号−1
def _get_month_index(dt: datetime) -> int:
    """
    寅月を1とした月番号の簡易版。
    本来は節入りで月が変わるが、ここではざっくりグレゴリオ暦の月で近似。
    2月 → 寅月(1), 3月 → 卯月(2), ..., 1月 → 丑月(12)
    """
    m = dt.month
    # 2月を1としてローテーション
    idx = (m - 2) % 12 + 1
    return idx


def _get_month_pillar(dt: datetime, year_pillar: str):
    """
    月柱を求める簡易ロジック
    ・寅月 = 1 として月番号を計算
    ・月支：寅から順に
    ・月干：年干の位置＋月番号−1
    """
    month_index = _get_month_index(dt)  # 1〜12

    # 月支：寅(寅=2番目)からスタート
    month_branch = JUNISHI[(2 + month_index - 1) % 12]  # 寅を起点

    # 年干
    year_stem = year_pillar[0]  # 甲乙丙...

    # 年干のインデックス
    y_idx = TENKAN.index(year_stem)

    # 月干：年干＋月番号−1
    month_stem = TENKAN[(y_idx + month_index - 1) % 10]

    return month_stem + month_branch


# 4. 日柱の計算（基準日からの経過日で干支を求める）
# 日干支は「ある基準日が何の干支か」を決めて、そこからの経過日で算出できます。
# ここではよく使われる
# - 1984-02-02 を 甲子日
# として扱います。
def _get_day_pillar(dt: datetime) -> str:
    """
    日柱（その日の干支）を求める。
    ・1984-02-02 を 甲子日 として基準にする。
    """
    base = date(1984, 2, 2)  # 甲子日（近似）
    delta = dt.date() - base
    idx = delta.days % 60
    return _KANSHI[idx]


# 5. 時柱の計算（時刻＋日干から求める）
# 四柱推命の時柱は
# - 時刻 → 地支（2時間ごと）
# - 日干＋時支 → 時干
# というルールです。
def _get_hour_branch(hour: int) -> str:
    """
    時刻（0〜23）から時支を求める。
    子：23〜1時、丑：1〜3時... だが、
    ここでは簡易的に
    23,0 → 子
    1,2 → 丑
    3,4 → 寅
    ...
    とする。
    """
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
def get_meishiki(dt: datetime) -> dict:
    """
    与えられた日時から
    ・年柱
    ・月柱
    ・日柱
    ・時柱
    を簡易計算する。
    """
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
