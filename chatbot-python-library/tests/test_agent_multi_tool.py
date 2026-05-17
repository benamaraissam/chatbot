"""Agent loop executes every tool call in a single model turn."""

from collections.abc import AsyncIterator
from typing import Any

import pytest

from chatbot.core.agent import AgentLoop
from chatbot.core.context import ToolContext, UserContext
from chatbot.core.events import ToolCallStart, ToolResult
from chatbot.providers.base import BaseProvider, ProviderConfig, ProviderMessage, ProviderStreamChunk
from chatbot.tools.registry import ToolRegistry


class MultiToolProvider(BaseProvider):
    name = "openai"

    def pydantic_ai_model(self) -> str:
        return "test"

    async def stream(
        self,
        messages: list[ProviderMessage],
        *,
        system_prompt: str | None = None,
        tools_schema: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        if any(m.role == "tool" for m in messages):
            yield ProviderStreamChunk(text_delta="All done.")
            yield ProviderStreamChunk(
                finish_reason="stop",
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            )
            return

        yield ProviderStreamChunk(
            tool_call_id="call_a",
            tool_name="get_weather",
            tool_input={},
        )
        yield ProviderStreamChunk(tool_input_delta='{"city":"Paris"}', tool_call_id="call_a")
        yield ProviderStreamChunk(
            tool_call_id="call_b",
            tool_name="search_docs",
            tool_input={},
        )
        yield ProviderStreamChunk(
            tool_input_delta='{"query":"events","limit":2}',
            tool_call_id="call_b",
        )
        yield ProviderStreamChunk(
            finish_reason="tool_calls",
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )


@pytest.mark.asyncio
async def test_agent_runs_all_tools_in_one_turn():
    tools = ToolRegistry()

    @tools.register
    async def get_weather(ctx, city: str = "Paris") -> dict:
        return {"city": city}

    @tools.register
    async def search_docs(ctx, query: str, limit: int = 3) -> dict:
        return {"query": query, "hits": limit}

    agent = AgentLoop(MultiToolProvider(ProviderConfig(model="test")), tools)
    ctx = ToolContext(user=UserContext(id="u1"))

    starts: list[str] = []
    results: list[tuple[str, bool]] = []

    async for event in agent.run([ProviderMessage(role="user", content="run both")], ctx):
        if isinstance(event, ToolCallStart):
            starts.append(event.id)
        if isinstance(event, ToolResult):
            results.append((event.id, event.is_error))

    assert starts == ["call_a", "call_b"]
    assert results == [("call_a", False), ("call_b", False)]
