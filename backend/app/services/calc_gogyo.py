# 十干 → 五行マッピング
STEM_TO_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

# 十二支 → 五行（蔵干ベース）マッピング
# 十二支は単独の五行ではなく、**蔵干（内部に含む干）**を使うのが一般的です。
# 簡易版として「主蔵干のみ」を採用します。
BRANCH_TO_MAIN_STEM = {
    "子": "癸",  # 水
    "丑": "己",  # 土
    "寅": "甲",  # 木
    "卯": "乙",  # 木
    "辰": "戊",  # 土
    "巳": "丙",  # 火
    "午": "丁",  # 火
    "未": "己",  # 土
    "申": "庚",  # 金
    "酉": "辛",  # 金
    "戌": "戊",  # 土
    "亥": "壬"   # 水
}

# 五行カウンターの初期化
def init_wuxing():
    return {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}


# 干支 → 五行を加算する関数
def add_pillar_to_wuxing(pillar: str, wuxing: dict):
    """
    pillar: '甲子' のような2文字
    wuxing: 五行カウンター
    """
    stem = pillar[0]   # 十干
    branch = pillar[1] # 十二支

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



# 命式（年柱・月柱・日柱・時柱）から五行バランスを計算
def calc_wuxing_balance(meishiki: dict):
    """
    meishiki = {
        "年柱": "乙卯",
        "月柱": "戊寅",
        "日柱": "辛巳",
        "時柱": "乙卯"
    }
    """
    wuxing = init_wuxing()

    for pillar in meishiki.values():
        add_pillar_to_wuxing(pillar, wuxing)

    return wuxing



# あなたが示した文章の五行バランスとほぼ一致します。



# これでできること
# この五行バランスを使って：
# - 木が強い → 人間関係・成長・行動力
# - 火がある → 情熱・表現
# - 土が少ない → 安定性の課題
# - 金が弱い → 日主が試練を受けやすい
# - 水がゼロ → 思考・柔軟性が弱め
# などの解釈をAIに渡すと、
# あなたが書いたような 高品質な鑑定文 を生成できます。

# 次に進められること
# - 五行バランス → 性格・運勢の解釈ロジック
# - AIに渡すプロンプトテンプレート
# - 桃源紀行風の文章生成テンプレート
# どれを作りましょうか。

