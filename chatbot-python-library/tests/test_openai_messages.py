"""OpenAI request body helpers."""

from chatbot.providers.base import ProviderMessage
from chatbot.providers.openai_messages import provider_message_to_openai, should_include_stream_usage


def test_provider_message_user_text():
    assert provider_message_to_openai(
        ProviderMessage(role="user", content="hi"),
    ) == {"role": "user", "content": "hi"}


def test_provider_message_assistant_tool_calls():
    msg = provider_message_to_openai(
        ProviderMessage(
            role="assistant",
            content=None,
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"city":"Paris"}'},
                }
            ],
        )
    )
    assert msg["role"] == "assistant"
    assert msg["content"] is None
    assert msg["reasoning_content"] == ""
    assert len(msg["tool_calls"]) == 1


def test_provider_message_assistant_tool_calls_with_reasoning():
    msg = provider_message_to_openai(
        ProviderMessage(
            role="assistant",
            content="Calling tools",
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": "{}"},
                }
            ],
            reasoning_content="Let me check the weather.",
        )
    )
    assert msg["reasoning_content"] == "Let me check the weather."


def test_provider_message_tool_result():
    msg = provider_message_to_openai(
        ProviderMessage(
            role="tool",
            tool_call_id="call_1",
            content='{"temp": 18}',
        )
    )
    assert msg == {"role": "tool", "tool_call_id": "call_1", "content": '{"temp": 18}'}


def test_stream_usage_default_off_for_moonshot():
    assert not should_include_stream_usage("https://api.moonshot.ai/v1/chat/completions")


def test_stream_usage_on_for_openai():
    assert should_include_stream_usage("https://api.openai.com/v1/chat/completions")
