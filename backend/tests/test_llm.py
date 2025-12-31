import pytest
from app.services.litellm_adapter import make_analysis_detail, make_analysis_summary


@pytest.mark.asyncio
async def test_make_analysis_detail_with_ci_fixture():
    result = await make_analysis_detail("システム＿プロンプト", "ユーザープロンプト")

    assert result == "[FAKE RESP] model=gemini/gemini-2.5-flash system_prompt=システム＿プロンプト user_prompt=ユーザープロンプト"


@pytest.mark.asyncio
async def test_make_analysis_summary_with_ci_fixture():
    result = await make_analysis_summary("システム＿プロンプト", "ユーザープロンプト")
    assert result == "[FAKE RESP] model=gemini/gemini-2.5-flash-lite system_prompt=システム＿プロンプト user_prompt=ユーザープロンプト"
