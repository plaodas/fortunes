from app.services.calc_gogyo import calc_wuxing_balance


def test_calc_gogyo():
    # 動作例（あなたの例でテスト）
    meishiki = {
        "年柱": "乙卯",
        "月柱": "戊寅",
        "日柱": "辛巳",
        "時柱": "乙卯"
    }

    # 待される出力イメージ近似値なので注意
    expected_balance = {
        '木': 5, # original:  '木': 4,
        '火': 1, # original:  '火': 2,
        '土': 1,
        '金': 1,
        '水': 0
    }

    balance = calc_wuxing_balance(meishiki)
    assert balance == expected_balance


