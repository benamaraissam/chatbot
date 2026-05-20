"""Tests for chatbot.providers.anthropic — event parsing and config wiring."""
from __future__ import annotations

import pytest

from chatbot.providers.anthropic import AnthropicProvider, _parse_anthropic_event


# ─────────────────────────────────────────────────────────────────────────────
# _parse_anthropic_event — pure event-shape mapping
# ─────────────────────────────────────────────────────────────────────────────

def test_parses_text_delta_event() -> None:
    chunk = _parse_anthropic_event(
        {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "hi"}}
    )
    assert chunk is not None
    assert chunk.text_delta == "hi"


def test_parses_input_json_delta_event() -> None:
    chunk = _parse_anthropic_event(
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": '{"city":'},
        }
    )
    assert chunk is not None
    assert chunk.tool_call_id == 0
    assert chunk.tool_input_delta == '{"city":'


def test_parses_tool_use_content_block_start() -> None:
    chunk = _parse_anthropic_event(
        {
            "type": "content_block_start",
            "content_block": {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "get_weather",
            },
        }
    )
    assert chunk is not None
    assert chunk.tool_call_id == "toolu_1"
    assert chunk.tool_name == "get_weather"
    assert chunk.tool_input == {}


def test_parses_message_delta_with_usage() -> None:
    chunk = _parse_anthropic_event(
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn"},
            "usage": {"input_tokens": 10, "output_tokens": 30},
        }
    )
    assert chunk is not None
    assert chunk.finish_reason == "end_turn"
    assert chunk.usage["prompt_tokens"] == 10
    assert chunk.usage["completion_tokens"] == 30
    assert chunk.usage["total_tokens"] == 40


def test_parses_message_delta_without_usage_defaults_to_zero() -> None:
    chunk = _parse_anthropic_event(
        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}}
    )
    assert chunk is not None
    assert chunk.usage["prompt_tokens"] == 0
    assert chunk.usage["completion_tokens"] == 0
    assert chunk.usage["total_tokens"] == 0


def test_returns_none_for_irrelevant_event_types() -> None:
    assert _parse_anthropic_event({"type": "ping"}) is None
    assert _parse_anthropic_event({"type": "message_start"}) is None


def test_returns_none_for_content_block_delta_of_unknown_subtype() -> None:
    assert (
        _parse_anthropic_event(
            {
                "type": "content_block_delta",
                "delta": {"type": "thinking_delta", "text": "..."},
            }
        )
        is None
    )


# ─────────────────────────────────────────────────────────────────────────────
# Provider configuration
# ─────────────────────────────────────────────────────────────────────────────

def _make_provider(monkeypatch: pytest.MonkeyPatch) -> AnthropicProvider:
    from chatbot.providers.base import ProviderConfig

    # Construct a ProviderConfig the same way the agent setup would.
    cfg = ProviderConfig(model="claude-3-5-sonnet")
    return AnthropicProvider(cfg)


def test_pydantic_ai_model_string(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = _make_provider(monkeypatch)
    assert provider.pydantic_ai_model() == "anthropic:claude-3-5-sonnet"


def test_messages_url_uses_default_when_no_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    provider = _make_provider(monkeypatch)
    assert provider.messages_url().startswith("https://api.anthropic.com/")


def test_messages_url_honours_anthropic_base_url_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://proxy.example.com")
    provider = _make_provider(monkeypatch)
    assert provider.messages_url().startswith("https://proxy.example.com/")


async def test_stream_raises_when_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = _make_provider(monkeypatch)

    from chatbot.providers.base import ProviderMessage

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        # Consume the async generator to trigger the API key check.
        agen = provider.stream([ProviderMessage(role="user", content="hi")])
        await agen.__anext__()
