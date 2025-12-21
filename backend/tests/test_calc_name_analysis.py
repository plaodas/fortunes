from app.services.calc_name_analysis import get_gogaku


def test_gogaku():
    sei = [("山", 3), ("田", 5)]
    mei = [("太", 4), ("郎", 9)]
    result = get_gogaku(sei, mei)
    assert result == {"天格": 8, "人格": 9, "地格": 13, "外格": 12, "総格": 21}  # 3 + 5  # 5 + 4  # 4 + 9  # (3 + 4 + 9) - (5 + 4)  # 3 + 5 + 4 + 9
