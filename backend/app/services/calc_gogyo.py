"""
五行算出ロジック

こでは、命式（年柱・月柱・日柱・時柱）から五行バランスを計算するロジックを、Pythonでそのまま使える形にまとめます。
四柱推命では
- 十干 → 五行
- 十二支 → 五行（蔵干を含む）
を数えて、最終的に 木・火・土・金・水の強弱 を出します。
"""

from .constants import BRANCH_TO_MAIN_STEM, STEM_TO_ELEMENT


# 五行カウンターの初期化
def _init_wuxing() -> dict[str, int]:
    return {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}


# 干支 → 五行を加算する関数
def _add_pillar_to_wuxing(pillar: str, wuxing: dict[str, int]) -> dict[str, int]:
    """
    pillar: '甲子' のような2文字
    wuxing: 五行カウンター
    """
    stem = pillar[0]  # 十干
    branch = pillar[1]  # 十二支

    # 十干の五行
    stem_ele = STEM_TO_ELEMENT.get(stem)
    if stem_ele:
        wuxing[stem_ele] += 1

    # 十二支の五行（主蔵干）
    main_stem = BRANCH_TO_MAIN_STEM.get(branch)
    if main_stem:
        branch_ele = STEM_TO_ELEMENT.get(main_stem)
        if branch_ele:
            wuxing[branch_ele] += 1

    return wuxing


# 命式（年柱・月柱・日柱・時柱）から五行バランスを計算
def calc_wuxing_balance(meishiki: dict[str, str]) -> dict[str, int]:
    """
    arg meishiki: {'年柱':'乙卯', '月柱':'戊寅', '日柱':'辛巳', '時柱':'乙卯'}
    return: {'木':4, '火':2, '土':1, '金':1, '水':0}
    """
    wuxing = _init_wuxing()

    for pillar in meishiki.values():
        wuxing = _add_pillar_to_wuxing(pillar, wuxing)

    return wuxing


# これでできること
# この五行バランスを使って：
# - 木が強い → 人間関係・成長・行動力
# - 火がある → 情熱・表現
# - 土が少ない → 安定性の課題
# - 金が弱い → 日主が試練を受けやすい
# - 水がゼロ → 思考・柔軟性が弱め
# などの解釈をAIに渡すと、
# あなたが書いたような 高品質な鑑定文 を生成できます。
