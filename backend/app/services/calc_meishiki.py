from datetime import date, datetime
from ..entities.birth_analytics import Meishiki

# 十干と十二支
TENKAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JUNISHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 甲子を基準にした60干支
KANSHI = [TENKAN[i % 10] + JUNISHI[i % 12] for i in range(60)]

def get_year_pillar(dt: datetime):
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
    return KANSHI[idx]

def get_month_index(dt: datetime):
    """
    寅月を1とした月番号の簡易版。
    本来は節入りで月が変わるが、ここではざっくりグレゴリオ暦の月で近似。
    2月 → 寅月(1), 3月 → 卯月(2), ..., 1月 → 丑月(12)
    """
    m = dt.month
    # 2月を1としてローテーション
    idx = (m - 2) % 12 + 1
    return idx

def get_month_pillar(dt: datetime, year_pillar: str):
    """
    月柱を求める簡易ロジック
    ・寅月 = 1 として月番号を計算
    ・月支：寅から順に
    ・月干：年干の位置＋月番号−1
    """
    month_index = get_month_index(dt)  # 1〜12

    # 月支：寅(寅=2番目)からスタート
    month_branch = JUNISHI[(2 + month_index - 1) % 12]  # 寅を起点

    # 年干
    year_stem = year_pillar[0]  # 甲乙丙...

    # 年干のインデックス
    y_idx = TENKAN.index(year_stem)

    # 月干：年干＋月番号−1
    month_stem = TENKAN[(y_idx + month_index - 1) % 10]

    return month_stem + month_branch

def get_day_pillar(dt: datetime):
    """
    日柱（その日の干支）を求める。
    ・1984-02-02 を 甲子日 として基準にする。
    """
    base = date(1984, 2, 2)  # 甲子日（近似）
    delta = dt.date() - base
    idx = delta.days % 60
    return KANSHI[idx]

def get_hour_branch(hour: int):
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

# 日干×時支 → 時干のテーブル（簡略版、よく使われる対応）
# 実務書に載っている「日干別の時干一覧」を元に自作してもOK
HOUR_STEM_TABLE = {
    "甲": ["甲","丙","戊","庚","壬","甲","丙","戊","庚","壬","甲","丙"],
    "乙": ["乙","丁","己","辛","癸","乙","丁","己","辛","癸","乙","丁"],
    "丙": ["丙","戊","庚","壬","甲","丙","戊","庚","壬","甲","丙","戊"],
    "丁": ["丁","己","辛","癸","乙","丁","己","辛","癸","乙","丁","己"],
    "戊": ["戊","庚","壬","甲","丙","戊","庚","壬","甲","丙","戊","庚"],
    "己": ["己","辛","癸","乙","丁","己","辛","癸","乙","丁","己","辛"],
    "庚": ["庚","壬","甲","丙","戊","庚","壬","甲","丙","戊","庚","壬"],
    "辛": ["辛","癸","乙","丁","己","辛","癸","乙","丁","己","辛","癸"],
    "壬": ["壬","甲","丙","戊","庚","壬","甲","丙","戊","庚","壬","甲"],
    "癸": ["癸","乙","丁","己","辛","癸","乙","丁","己","辛","癸","乙"],
}

def get_hour_pillar(dt: datetime, day_pillar: str):
    """
    時柱を求める
    ・時支：時刻から算出
    ・時干：日干＋時支の位置からテーブルで取得
    """
    h = dt.hour
    branch = get_hour_branch(h)
    day_stem = day_pillar[0]

    # 子〜亥を 0〜11 に対応
    b_idx = JUNISHI.index(branch)
    stem = HOUR_STEM_TABLE[day_stem][b_idx]

    return stem + branch

def get_meishiki(dt: datetime):
    """
    与えられた日時から
    ・年柱
    ・月柱
    ・日柱
    ・時柱
    を簡易計算する。
    """
    year_p = get_year_pillar(dt)
    month_p = get_month_pillar(dt, year_p)
    day_p = get_day_pillar(dt)
    hour_p = get_hour_pillar(dt, day_p)

    return Meishiki(
        year=year_p,
        month=month_p,
        day=day_p,
        hour=hour_p,
    )

