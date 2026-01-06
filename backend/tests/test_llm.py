import pytest
from app.services.litellm_adapter import LiteLlmAdapter


@pytest.mark.asyncio
async def test_make_analysis_detail_with_ci_fixture():
    lite_llm_adapter = LiteLlmAdapter(provider="vertex_ai", model="gemini/gemini-2.5-flash")
    llm_response = await lite_llm_adapter.make_analysis(1, system_prompt="システム＿プロンプト", user_prompt="ユーザープロンプト")

    assert llm_response.response_text == "[FAKE RESP] model=gemini/gemini-2.5-flash system_prompt=システム＿プロンプト user_prompt=ユーザープロンプト"
