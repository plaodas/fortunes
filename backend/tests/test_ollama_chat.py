import pytest
from app.services.litellm_adapter import LiteLlmAdapter

# conftest が _call_llm をフェイクに差し替える前の実装を保持する。
_real_call_llm = LiteLlmAdapter._call_llm

MESSAGES = [{"role": "user", "content": "こんにちは"}]


class _Response:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _Client:
    seen: dict = {}
    payload: dict = {"message": {"role": "assistant", "content": "物語"}}

    def __init__(self, *args, **kwargs):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json):
        _Client.seen = {"url": url, "json": json}
        return _Response(_Client.payload)


@pytest.fixture
def ollama(monkeypatch):
    import app.services.litellm_adapter as adapter_mod

    monkeypatch.setattr(adapter_mod.httpx, "AsyncClient", _Client)
    monkeypatch.setattr(LiteLlmAdapter, "_call_llm", _real_call_llm)
    _Client.seen = {}
    _Client.payload = {"message": {"role": "assistant", "content": "物語"}, "model": "qwen3.5:4b"}
    adapter = LiteLlmAdapter(provider="ollama", model="ollama/qwen3.5:4b")
    adapter.api_base = "http://ollama:11434"
    return adapter


@pytest.mark.asyncio
async def test_qwen3_sends_think_false(ollama):
    data = await ollama._call_llm("ollama/qwen3.5:4b", 0.8, 0, MESSAGES)

    body = _Client.seen["json"]
    assert _Client.seen["url"] == "http://ollama:11434/api/chat"
    assert body["model"] == "qwen3.5:4b"
    assert body["stream"] is False
    assert body["think"] is False
    assert body["options"]["num_predict"] == 1200
    assert data["message"]["content"] == "物語"


@pytest.mark.asyncio
async def test_qwen25_omits_think(ollama):
    await ollama._call_llm("ollama/qwen3.5:4b", 0.8, 0, MESSAGES)

    assert "think" not in _Client.seen["json"]
    assert _Client.seen["json"]["model"] == "qwen3.5:4b"


@pytest.mark.asyncio
async def test_empty_content_raises(ollama):
    _Client.payload = {"message": {"role": "assistant", "content": "  "}}

    with pytest.raises(RuntimeError, match="empty"):
        await ollama.make_analysis(1, "system", "user")
