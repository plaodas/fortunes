import pytest
from app.services.ollama_adapter import OllamaAdapter


@pytest.mark.asyncio
async def test_make_analysis_detail_with_ci_fixture():
    adapter = OllamaAdapter(provider="vertex_ai", model="gemini/gemini-2.5-flash")
    llm_response = await adapter.make_analysis(1, system_prompt="システム＿プロンプト", user_prompt="ユーザープロンプト")

    assert llm_response.response_text == "[FAKE RESP] model=gemini/gemini-2.5-flash system_prompt=システム＿プロンプト user_prompt=ユーザープロンプト"
