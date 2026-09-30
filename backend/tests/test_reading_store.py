from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.reading_store import build_stored_reading


def test_build_stored_reading_returns_charts() -> None:
    birth = datetime(1990, 1, 1, 12, tzinfo=ZoneInfo("Asia/Tokyo"))
    result_birth, result_name, prompt = build_stored_reading(birth, "female", [("太", 4)], [("郎", 13)])

    meishiki = result_birth["meishiki"]
    assert meishiki["year"]
    assert meishiki["strength"]
    assert meishiki["pillars"]["day"]["tsuhen"]
    assert meishiki["daiun"]
    assert meishiki["daiun"][0]["start"].endswith("ヶ月")
    assert set(result_birth["gogyo"]) == {"wood", "fire", "earth", "metal", "water"}
    assert set(result_name) >= {"tenkaku", "jinkaku", "chikaku", "gaikaku", "soukaku"}
    assert "四柱" in prompt and "五格" in prompt
