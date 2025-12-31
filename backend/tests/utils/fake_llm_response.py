from typing import Any, Dict


def fake_llm_response(model: str, messages: list[dict[str, str]]) -> Dict[str, Any]:
    """Fake LLM response for testing."""
    return {
        "id": "fake-response-id",
        "model": model,
        "usage": {
            "total_tokens": 617,
            "prompt_tokens": 522,
            "completion_tokens": 95,
            "prompt_tokens_details": {"text_tokens": 522, "audio_tokens": None, "image_tokens": None, "cached_tokens": None},
            "completion_tokens_details": None,
        },
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "images": [],
                    "content": f"[FAKE RESP] model={model} system_prompt={messages[0]['content'][:80]} user_prompt={messages[1]['content'][:80]}",
                    "tool_calls": None,
                    "function_call": None,
                    "thinking_blocks": [],
                },
                "finish_reason": "stop",
            }
        ],
        "created": 1767148127,
        "system_fingerprint": None,
        "vertex_ai_safety_results": [],
        "vertex_ai_citation_metadata": [],
        "vertex_ai_grounding_metadata": [],
        "vertex_ai_url_context_metadata": [],
    }
