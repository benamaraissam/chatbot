"""Tests for the streaming event taxonomy."""
from __future__ import annotations

from chatbot.core.events import (
    MessageStart,
    TextDelta,
    ThinkingDelta,
    ToolCallDelta,
    ToolCallEnd,
    ToolCallStart,
)


def test_message_start_payload_shape() -> None:
    ev = MessageStart(id="m_1", role="assistant")
    assert ev.event_type == "message_start"
    assert ev.to_payload() == {"id": "m_1", "role": "assistant"}


def test_text_delta_payload_shape() -> None:
    ev = TextDelta(delta="hello")
    assert ev.event_type == "text_delta"
    assert ev.to_payload() == {"delta": "hello"}


def test_thinking_delta_payload_shape() -> None:
    ev = ThinkingDelta(delta="reasoning...")
    assert ev.event_type == "thinking_delta"
    assert ev.to_payload() == {"delta": "reasoning..."}


def test_tool_call_start_payload_includes_input() -> None:
    ev = ToolCallStart(id="t_1", name="get_weather", input={"city": "Paris"})
    assert ev.event_type == "tool_call_start"
    assert ev.to_payload() == {
        "id": "t_1",
        "name": "get_weather",
        "input": {"city": "Paris"},
    }


def test_tool_call_delta_uses_camel_case_input_delta() -> None:
    ev = ToolCallDelta(id="t_1", input_delta='{"par')
    # The wire field name must be camelCase for the frontend.
    assert ev.to_payload() == {"id": "t_1", "inputDelta": '{"par'}


def test_tool_call_end_payload_shape() -> None:
    ev = ToolCallEnd(id="t_1")
    assert ev.to_payload() == {"id": "t_1"}


def test_events_are_immutable() -> None:
    # Frozen dataclasses — mutation should fail at runtime.
    import pytest

    ev = TextDelta(delta="x")
    with pytest.raises(Exception):
        ev.delta = "y"  # type: ignore[misc]
