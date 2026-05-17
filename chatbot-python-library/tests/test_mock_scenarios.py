"""Mock provider scenario routing tests."""

import pytest

from chatbot import Chatbot, ToolRegistry
from chatbot.core.events import (
    Done,
    TextDelta,
    ThinkingDelta,
    ToolApprovalRequired,
    ToolCallDelta,
    ToolCallEnd,
    ToolCallStart,
    ToolResult,
)
from chatbot.providers.mock_scenarios import MockScenario, match_scenario


def test_match_scenario_keywords():
    assert match_scenario("full demo", 0).scenario == MockScenario.FULL
    assert match_scenario("weather in Paris", 0).scenario == MockScenario.WEATHER
    assert match_scenario("thinking please", 0).scenario == MockScenario.THINKING
    assert match_scenario("send approval email", 0).scenario == MockScenario.APPROVAL


@pytest.fixture
def demo_bot():
    tools = ToolRegistry()

    @tools.register
    async def get_weather(ctx, city: str = "Paris") -> dict:
        return {"city": city, "temp": 20}

    @tools.register(requires_approval=True)
    async def send_email(ctx, to: str, subject: str, body: str) -> dict:
        return {"sent": True}

    @tools.register
    async def simulate_failure(ctx, reason: str = "x") -> dict:
        raise RuntimeError(reason)

    return Chatbot(default_provider="mock", storage="memory", tools=tools)


@pytest.mark.asyncio
async def test_thinking_delta_stream(demo_bot):
    saw_thinking = False
    async for event in demo_bot.stream("thinking demo"):
        if isinstance(event, ThinkingDelta):
            saw_thinking = True
    assert saw_thinking


@pytest.mark.asyncio
async def test_weather_tool_stream_events(demo_bot):
    types: list[str] = []
    async for event in demo_bot.stream("weather in Tokyo"):
        types.append(event.event_type)
    assert "tool_call_start" in types
    assert "tool_call_delta" in types
    assert "tool_call_end" in types
    assert "tool_result" in types
    assert "text_delta" in types
    assert types[-1] == "done" or "done" in types


@pytest.mark.asyncio
async def test_approval_required(demo_bot):
    saw_approval = False
    async for event in demo_bot.stream("send approval email"):
        if isinstance(event, ToolApprovalRequired):
            saw_approval = True
            assert event.name == "send_email"
    assert saw_approval


@pytest.mark.asyncio
async def test_tool_error_yields_error_result(demo_bot):
    saw_error = False
    async for event in demo_bot.stream("error demo"):
        if isinstance(event, ToolResult) and event.is_error:
            saw_error = True
    assert saw_error
