"""Unit tests for OpenAI SSE chunk parsing (reasoning + tool calls)."""

from chatbot.providers.openai import _OpenAIStreamState, _parse_openai_payload


def test_reasoning_content_emits_thinking_delta():
    state = _OpenAIStreamState()
    chunks = _parse_openai_payload(
        {
            "choices": [
                {
                    "delta": {"reasoning_content": "Let me think about this."},
                    "finish_reason": None,
                }
            ]
        },
        state,
    )
    thinking = [c for c in chunks if c.thinking_delta]
    assert thinking
    assert "".join(c.thinking_delta for c in thinking) == "Let me think about this."


def test_content_emits_text_delta():
    state = _OpenAIStreamState()
    chunks = _parse_openai_payload(
        {
            "choices": [
                {"delta": {"content": "Hello"}, "finish_reason": None},
            ]
        },
        state,
    )
    text = [c for c in chunks if c.text_delta]
    assert "".join(c.text_delta for c in text) == "Hello"


def test_tool_calls_accumulate_across_chunks():
    state = _OpenAIStreamState()
    first = _parse_openai_payload(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_abc",
                                "function": {"name": "get_weather", "arguments": ""},
                            }
                        ]
                    }
                }
            ]
        },
        state,
    )
    starts = [c for c in first if c.tool_name]
    assert len(starts) == 1
    assert starts[0].tool_call_id == "call_abc"
    assert starts[0].tool_name == "get_weather"

    second = _parse_openai_payload(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "function": {"arguments": '{"city":'},
                            }
                        ]
                    }
                }
            ]
        },
        state,
    )
    deltas = [c for c in second if c.tool_input_delta]
    assert deltas
    assert deltas[0].tool_input_delta == '{"city":'
