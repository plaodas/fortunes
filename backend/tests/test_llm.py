import os

import litellm
from app.services.litellm_adapter import make_analysis_summary
from app.services.prompts.template_life_analysis_summary import TEMPLATE_SUMMARY_SYSTEM


def test_make_analysis_summary() -> dict:
    os.environ["DEBUG_LITELLM_FAKE_RESP"] = "0"
    litellm._turn_on_debug()

    system_prompt = TEMPLATE_SUMMARY_SYSTEM
    user_prompt = """わたしの人生の“今のテーマ”を200文字以内でまとめてください。

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
    result: dict = make_analysis_summary(system_prompt, user_prompt)
    print(result)
    expect_result = """[FAKE RESP] model=gemini-1.5-pro system_prompt_preview=
あなたは「人生という桃源郷を巡る旅」の案内人です。
四柱推命・五行バランス・姓名判断の情報をもとに、
読み手の人生の“今のテーマ”を200文字以内でまとめてく user_prompt_preview=わたしの人生の“今のテーマ”を200文字以内でまとめてください。

========================
【四柱推命：命式の要点】
年柱：乙卯（家系"""
    assert result == expect_result
