from typing import Any, Dict

fake_llm_response_template: Dict[str, Any] = {
    "id": "YIpUacCjHJHG2roPuofg6Aw",
    "model": "gemini-2.5-flash-lite",
    "usage": {
        "total_tokens": 617,
        "prompt_tokens": 522,
        "completion_tokens": 95,
        "prompt_tokens_details": {"text_tokens": 522, "audio_tokens": None, "image_tokens": None, "cached_tokens": None},
        "completion_tokens_details": None,
    },
    "object": "chat.completion",
    "choices": [
        {"index": 0, "message": {"role": "assistant", "images": [], "content": "MESSAGE_TRUNCATED", "tool_calls": None, "function_call": None, "thinking_blocks": []}, "finish_reason": "stop"}
    ],
    "created": 1767148127,
    "system_fingerprint": None,
    "vertex_ai_safety_results": [],
    "vertex_ai_citation_metadata": [],
    "vertex_ai_grounding_metadata": [],
    "vertex_ai_url_context_metadata": [],
}
