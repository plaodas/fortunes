"""
deprecated: birth_analysis.pyに移管したので不使用
"""

from app.services.calc_gogyo_interpretation import interpret_wuxing

def test_calc_gogyo_balance():

    # 5. 実行例（辛巳 → 日主は「金」）
    balance = {"木":4, "火":2, "土":1, "金":1, "水":0}
    result = interpret_wuxing(balance, "辛")

    # 出力イメージ
    expected_result = {
        '日主': '金',
        '強い五行': ['木'],
        '弱い五行': ['水'],
        '性格': [
            '人との縁が強く、成長意欲が高い。新しいことに挑戦する力がある。'
        ],
        '課題': [
            '考えすぎたり、逆に思考が浅くなったりする。柔軟性が不足しがち。'
        ],
        '相性': [
            'あなた（日主：金）を助けるのは「水」の気。',
            'あなたを消耗させやすいのは「木」の気。'
        ]
    }

    assert result == expected_result
