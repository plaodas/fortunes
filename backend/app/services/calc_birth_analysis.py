"""
四柱＋五行を統合した総合鑑定ロジック（完全版）

総合鑑定は以下の4つの要素を統合して作ります。
- 四柱の意味（家系・社会・本人・晩年）
- 干支の性質（十干＋十二支）
- 五行バランス（強い・弱い）
- 日主（本人の五行）との相生・相剋
これらをすべてロジック化し、
AIに渡す前の“構造化された鑑定データ” を作ります。
"""
# 0. 必要なインポート
from app.services.constants import BRANCH_TRAITS, PILLAR_MEANING, STEM_TRAITS, WUXING_TRAITS, STEM_TO_ELEMENT, XIANGSHENG, XIANGKE

# 1. 四柱の解釈ロジック（前回作ったロジックを統合）
def interpret_pillar(pillar_name: str, kanshi: str):
    stem = kanshi[0]
    branch = kanshi[1]

    stem_trait = STEM_TRAITS.get(stem, "")
    branch_trait = BRANCH_TRAITS.get(branch, "")
    pillar_meaning = PILLAR_MEANING[pillar_name]

    return {
        "柱": pillar_name,
        "干支": kanshi,
        "領域": pillar_meaning,
        "十干の性質": stem_trait,
        "十二支の性質": branch_trait,
        "まとめ": f"{pillar_name}は{pillar_meaning}。{stem_trait}、{branch_trait}の性質が強く表れる。"
    }

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


# 2. 五行バランスの解釈（前回のロジックを統合）
def interpret_wuxing(balance: dict, day_stem: str):
    day_ele = STEM_TO_ELEMENT[day_stem]
    strong, weak = analyze_strength(balance)

    help_ele = XIANGSHENG[day_ele]
    harm_ele = XIANGKE[day_ele]

    return {
        "日主": day_ele,
        "強い五行": strong,
        "弱い五行": weak,
        "性格傾向": [WUXING_TRAITS[e]["強い"] for e in strong],
        "課題": [WUXING_TRAITS[e]["弱い"] for e in weak],
        "相性": {
            "助ける五行": help_ele,
            "弱らせる五行": harm_ele
        }
    }


# 3. 四柱＋五行を統合した総合鑑定ロジック
# ここが今回のメインです。
def synthesize_reading(meishiki: dict, balance: dict) -> dict:
    """
    arg:
      meishiki: {"年柱":"乙卯", "月柱":"戊寅", "日柱":"辛巳", "時柱":"乙卯"}
      balance: {'木':4,'火':2,'土':1,'金':1,'水':0}
    return:
      dict
    """

    # 日主（本人の五行）
    day_stem = meishiki["日柱"][0]

    # 四柱の解釈
    pillar_interpretations = {
        name: interpret_pillar(name, kanshi)
        for name, kanshi in meishiki.items()
    }

    # 五行バランスの解釈
    wuxing_interpretation = interpret_wuxing(balance, day_stem)

    # 総合まとめ（AIに渡す前の構造化データ）
    summary = {
        "四柱": pillar_interpretations,
        "五行バランス": wuxing_interpretation,
        "総合テーマ": {
            "性格": wuxing_interpretation["性格傾向"],
            "課題": wuxing_interpretation["課題"],
            "人生の流れ": [
                pillar_interpretations["年柱"]["まとめ"],
                pillar_interpretations["月柱"]["まとめ"],
                pillar_interpretations["日柱"]["まとめ"],
                pillar_interpretations["時柱"]["まとめ"]
            ]
        }
    }

    return summary




# 6. この構造化データをAIに渡すと…
# あなたが最初に示したような
# - 命式の特徴
# - 五行バランス
# - 総合的な傾向
# - 桃源紀行風の鑑定文
# を 安いモデルでも高品質に生成できます。
