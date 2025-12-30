import os

import litellm
import pytest
from app.services.litellm_adapter import make_analysis_summary
from app.services.prompts.template_life_analysis import TEMPLATE_DETAIL_SYSTEM
from app.services.prompts.template_life_analysis_summary import TEMPLATE_SUMMARY_SYSTEM


@pytest.mark.anyio
async def test_make_analysis_summary() -> None:
    os.environ["DEBUG_LITELLM_FAKE_RESP"] = "1"  # Enable fake response for testing
    # litellm._turn_on_debug() # comment in to enable litellm debug mode

    system_prompt = TEMPLATE_SUMMARY_SYSTEM
    user_prompt = """わたしの人生のテーマを150文字以内でまとめてください。
========================
【四柱推命：命式の要点】
年柱：乙卯（家系・幼少期・ルーツに影響。家族の価値観や幼少期の性質を示す。）
月柱：乙寅（社会・青年期・仕事運に影響。20〜40代の運勢や社会的立場を示す。）
日柱：庚辰（本人の本質・性格・結婚運を示す。人生の中心となる柱。）
時柱：丙卯（晩年運・子供運・才能を示す。後半生のテーマが表れる。）

【五行バランス】
日主：金
強み：['人との縁が強く、成長意欲が高い。新しいことに挑戦する力がある。']
課題：['考えすぎたり、逆に思考が浅くなったりする。柔軟性が不足しがち。']

【姓名判断：五格の印象】
天格：霧の向こうに光が見える。慎重に進めば道は整う。
人格：風向きが乱れ、足元に注意が必要な時期。
地格：霧の向こうに光が見える。慎重に進めば道は整う。
外格：風向きが乱れ、足元に注意が必要な時期。
総格：風向きが乱れ、足元に注意が必要な時期。
========================
"""

    result: str = await make_analysis_summary(system_prompt, user_prompt)
    print(result)
    expect_result = """[FAKE RESP] model=gemini/gemini-2.5-flash-lite system_prompt_preview=
あなたは「人生という桃源郷を巡る旅」の案内人です。
四柱推命・五行バランス・姓名判断の情報をもとに、
読み手の人生のテーマを150文字以内でまとめてください。 user_prompt_preview=わたしの人生のテーマを150文字以内でまとめてください。
========================
【四柱推命：命式の要点】
年柱：乙卯（家系・幼少期・"""
    print(expect_result)

    assert result == expect_result


@pytest.mark.anyio
async def test_make_analysis_detail() -> None:
    os.environ["DEBUG_LITELLM_FAKE_RESP"] = "1"  # Enable fake response for testing
    litellm._turn_on_debug()  # comment in to enable litellm debug mode

    system_prompt = TEMPLATE_DETAIL_SYSTEM

    user_prompt = """以下に、わたしの命式・五行バランス・姓名判断の結果を示します。

========================
【四柱推命：命式】
年柱：乙卯
　- 領域：家系・幼少期・ルーツに影響。家族の価値観や幼少期の性質を示す。
　- 十干の性質：柔らかく調和的。人間関係に強い。
　- 十二支の性質：社交性と調和。人間関係に恵まれる。

月柱：乙寅
　- 領域：社会・青年期・仕事運に影響。20〜40代の運勢や社会的立場を示す。
　- 十干の性質：柔らかく調和的。人間関係に強い。
　- 十二支の性質：行動力と勇気。リーダーシップ。

日柱：庚辰
　- 領域：本人の本質・性格・結婚運を示す。人生の中心となる柱。
　- 十干の性質：意志が強く、改革精神がある。
　- 十二支の性質：理想が高く、創造力がある。

時柱：丙卯
　- 領域：晩年運・子供運・才能を示す。後半生のテーマが表れる。
　- 十干の性質：明るく情熱的。表現力が豊か。
　- 十二支の性質：社交性と調和。人間関係に恵まれる。

========================
【五行バランス】
日主：金
強い五行：['木']
弱い五行：['水']
性格傾向：['人との縁が強く、成長意欲が高い。新しいことに挑戦する力がある。']
課題：['考えすぎたり、逆に思考が浅くなったりする。柔軟性が不足しがち。']
相性（助ける五行）：水
相性（弱らせる五行）：木

========================
【姓名判断：五格】
天格：25（半吉）
　→ 旅の兆し：桃源の谷間に薄い霧が立ちこめていますが、その奥には確かな光が宿っています。焦らず、足元を確かめながら進むことで、霧はやがて晴れ、道が姿を現すでしょう。

人格：14（凶）
　→ 旅の兆し：桃源の空に雲がかかり、風が少し荒れています。無理に進もうとすると枝に引っかかり、思わぬつまずきが生じることも。しかし、立ち止まり、周囲を見渡せば、避けるべき道と進むべき道が見えてきます。
地格：11（半吉）
　→ 旅の兆し：桃源の谷間に薄い霧が立ちこめていますが、その奥には確かな光が宿っています。焦らず、足元を確かめながら進むことで、霧はやがて晴れ、道が姿を現すでしょう。

外格：22（凶）
　→ 旅の兆し：桃源の空に雲がかかり、風が少し荒れています。無理に進もうとすると枝に引っかかり、思わぬつまずきが生じることも。しかし、立ち止まり、周囲を見渡せば、避けるべき道と進むべき道が見えてきます。

総格：36（凶）
　→ 旅の兆し：桃源の空に雲がかかり、風が少し荒れています。無理に進もうとすると枝に引っかかり、思わぬつまずきが生じることも。しかし、立ち止まり、周囲を見渡せば、避けるべき道と進むべき道が見えてきます。

========================
"""
    result: str = await make_analysis_summary(system_prompt, user_prompt)
    print(result)
    expect_result = """[FAKE RESP] model=gemini/gemini-2.5-flash-lite system_prompt_preview=
あなたは人生という広大な桃源郷を巡る旅の案内人です。
四柱推命と姓名判断の知識をもとに、読み手の人生を優しく照らす物語のような鑑定文を作成してください。

【 user_prompt_preview=以下に、わたしの命式・五行バランス・姓名判断の結果を示します。

========================
【四柱推命：命式】
年柱：乙卯
　- 領域："""
    print(expect_result)

    assert result == expect_result
