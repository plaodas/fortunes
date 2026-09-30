from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.calc_meishiki import get_meishiki
from app.services.calc_stars import calc_daiun, is_forward, ten_god, twelve_stage

JST = ZoneInfo("Asia/Tokyo")


def test_ten_god_examples():
    assert ten_god("甲", "甲") == "比肩"
    assert ten_god("甲", "乙") == "劫財"
    assert ten_god("甲", "丙") == "食神"
    assert ten_god("甲", "丁") == "傷官"
    assert ten_god("甲", "戊") == "偏財"
    assert ten_god("甲", "己") == "正財"
    assert ten_god("甲", "庚") == "七殺"
    assert ten_god("甲", "辛") == "正官"
    assert ten_god("甲", "壬") == "偏印"
    assert ten_god("甲", "癸") == "正印"


def test_twelve_stage_direction():
    assert twelve_stage("甲", "亥") == "長生"
    assert twelve_stage("甲", "子") == "沐浴"
    assert twelve_stage("乙", "午") == "長生"
    assert twelve_stage("乙", "巳") == "沐浴"


def test_daiun_direction_and_first_pillar():
    birth = datetime(2024, 2, 5, 12, tzinfo=JST)
    chart = get_meishiki(birth)
    assert is_forward(chart["年柱"][0], "male") is True
    assert is_forward(chart["年柱"][0], "female") is False

    forward = calc_daiun(birth, "male", chart["年柱"][0], chart["月柱"], chart["日柱"][0])
    backward = calc_daiun(birth, "female", chart["年柱"][0], chart["月柱"], chart["日柱"][0])
    assert len(forward) == 8
    assert forward[0]["干支"] == "丁卯"
    assert forward[1]["干支"] == "戊辰"
    assert backward[0]["干支"] == "乙丑"
    assert backward[1]["干支"] == "甲子"
    assert forward[0]["開始"].endswith("ヶ月")

    before_lichun = datetime(2024, 1, 10, 12, tzinfo=JST)
    yin_year = get_meishiki(before_lichun)
    assert yin_year["年柱"][0] == "癸"
    assert is_forward(yin_year["年柱"][0], "male") is False
    assert is_forward(yin_year["年柱"][0], "female") is True
