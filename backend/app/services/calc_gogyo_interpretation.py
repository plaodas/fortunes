"""
deprecated: birth_analysis.pyに移管したので不使用

五行バランス → 性格・運勢の解釈ロジック

五行の強弱から読み解くポイントは以下の3つです。
- どの五行が強いか（性格の核）
- どの五行が弱いか（課題・伸びしろ）
- 日主（本人の五行）との関係（相生・相剋）
これをすべてロジック化します。
"""

from typing import Any

# 1. 五行の意味辞書（性格・行動傾向）
# まずは五行ごとの基本性質を辞書化します。
from .constants import WUXING_TRAITS


# 2. 五行の強弱を判定するロジック
# 五行バランスは、命式から得られたカウント（例：木4 火2 土1 金1 水0）を使います。
def analyze_strength(balance: dict) -> tuple[list[str], list[str]]:
    """
    balance = {"木":4, "火":2, "土":1, "金":1, "水":0}
    """
    max_val = max(balance.values())
    min_val = min(balance.values())

    strong = [k for k, v in balance.items() if v == max_val]
    weak = [k for k, v in balance.items() if v == min_val]

    return strong, weak


# 3. 日主（本人の五行）との関係（相生・相剋）
# constants.py に定義済みの辞書を利用します。
from .constants import STEM_TO_ELEMENT, XIANGSHENG, XIANGKE


# 4. 五行バランス → 性格・運勢の解釈ロジック
# ここで、すべてを統合します。
def interpret_wuxing(balance: dict, day_stem: str) -> dict[str, Any]:
    """
    balance: 五行バランス {"木":4, "火":2, ...}
    day_stem: 日干（例：辛）
    """
    day_ele = STEM_TO_ELEMENT[day_stem]

    strong, weak = analyze_strength(balance)

    interpretation = {
        "日主": day_ele,
        "強い五行": strong,
        "弱い五行": weak,
        "性格": [],
        "課題": [],
        "相性": []
    }

    # 強い五行の性格
    for ele in strong:
        interpretation["性格"].append(WUXING_TRAITS[ele]["強い"])

    # 弱い五行の課題
    for ele in weak:
        interpretation["課題"].append(WUXING_TRAITS[ele]["弱い"])

    # 日主との関係
    # 日主を助ける五行
    help_ele = XIANGSHENG[day_ele]
    # 日主を弱らせる五行
    harm_ele = XIANGKE[day_ele]

    interpretation["相性"].append(f"あなた（日主：{day_ele}）を助けるのは「{help_ele}」の気。")
    interpretation["相性"].append(f"あなたを消耗させやすいのは「{harm_ele}」の気。")

    return interpretation





#  6. このロジックをAIに渡すと…
# この「解釈結果」をAIに渡せば、
# 高品質な鑑定文（桃源紀行風） を安いモデルでも生成できます。



