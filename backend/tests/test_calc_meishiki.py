from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.calc_meishiki import _get_hour_branch, get_meishiki
from app.services.solar_terms import lichun

JST = ZoneInfo("Asia/Tokyo")


def test_lichun_2024_matches_naoj_within_half_hour():
    # 国立天文台 令和6年暦要項: 立春は 2月4日 17時27分（中央標準時）
    expected = datetime(2024, 2, 4, 17, 27, tzinfo=JST)
    assert abs(lichun(2024) - expected) < timedelta(minutes=30)


def test_year_and_month_switch_at_lichun():
    before = get_meishiki(datetime(2024, 2, 4, 12, tzinfo=JST))
    after = get_meishiki(datetime(2024, 2, 4, 18, tzinfo=JST))
    assert before["年柱"] == "癸卯"
    assert before["月柱"] == "乙丑"
    assert after["年柱"] == "甲辰"
    assert after["月柱"] == "丙寅"


def test_day_pillar_epoch():
    # 令和6年1月1日の干支は甲子（国立天文台 暦象年表）
    assert get_meishiki(datetime(2024, 1, 1, 12, tzinfo=JST))["日柱"] == "甲子"
    assert get_meishiki(datetime(2024, 1, 2, 12, tzinfo=JST))["日柱"] == "乙丑"
    assert get_meishiki(datetime(1984, 3, 31, 12, tzinfo=JST))["日柱"] == "甲子"


def test_hour_branch_boundaries():
    assert _get_hour_branch(23) == "子"
    assert _get_hour_branch(0) == "子"
    assert _get_hour_branch(1) == "丑"
    assert _get_hour_branch(2) == "丑"


def test_late_zi_does_not_change_the_day_pillar():
    evening = get_meishiki(datetime(2024, 1, 1, 23, tzinfo=JST))
    assert evening["日柱"] == "甲子"
    assert evening["時柱"][1] == "子"


def test_month_stem_uses_wuhu_dun_for_jia_year():
    # 甲年の寅月は丙寅。2024-02-05 は立春後。
    chart = get_meishiki(datetime(2024, 2, 5, 12, tzinfo=timezone.utc))
    assert chart["年柱"][0] == "甲"
    assert chart["月柱"] == "丙寅"
