"""max_tool_rounds: configurability + graceful finalize.

When the agent exhausts its tool-call budget, it must not leave the UI hanging:
it should make one final no-tools call so the model produces a closing answer
from whatever it has gathered, then emit MessageEnd(finish_reason='max_tool_rounds').
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from chatbot import Chatbot
from chatbot.core.agent import AgentLoop
from chatbot.core.context import ToolContext, UserContext
from chatbot.core.events import ErrorEvent, MessageEnd, TextDelta, ToolResult
from chatbot.providers.base import (
    BaseProvider,
    ProviderConfig,
    ProviderMessage,
    ProviderStreamChunk,
)
from chatbot.tools.registry import ToolRegistry


class _InfiniteToolCaller(BaseProvider):
    """Provider that keeps requesting the same tool until the agent stops it.

    Tracks whether ``tools_schema`` was ``None`` on the most recent call — that
    flag is how we recognise the agent's wrap-up call.
    """

    name = "openai"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.tool_calls_emitted = 0
        self.no_tools_call_count = 0
        self.wrap_up_text = "Here is the summary based on what I gathered so far."

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
        if tools_schema is None:
            # This is the agent's wrap-up call. Emit a text answer.
            self.no_tools_call_count += 1
            for piece in self.wrap_up_text.split(" "):
                yield ProviderStreamChunk(text_delta=piece + " ")
            yield ProviderStreamChunk(
                finish_reason="stop",
                usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            )
            return

        # Normal call — request another tool.
        self.tool_calls_emitted += 1
        call_id = f"call_{self.tool_calls_emitted:03d}"
        yield ProviderStreamChunk(
            tool_call_id=call_id, tool_name="page", tool_input={}
        )
        yield ProviderStreamChunk(
            tool_input_delta=f'{{"offset": {self.tool_calls_emitted * 50}}}',
            tool_call_id=call_id,
        )
        yield ProviderStreamChunk(
            finish_reason="tool_calls",
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )


@pytest.fixture
def paginating_tools():
    tools = ToolRegistry()

    @tools.register
    async def page(ctx, offset: int = 0) -> dict:
        return {"offset": offset, "items": [{"i": i} for i in range(5)]}

    return tools


@pytest.fixture
def ctx():
    return ToolContext(user=UserContext(id="u1"))


@pytest.mark.asyncio
async def test_default_max_tool_rounds_is_10():
    """Default was 5 (too low for paginated workflows); should be 10 now."""
    agent = AgentLoop(_InfiniteToolCaller(ProviderConfig(model="test")), ToolRegistry())
    assert agent.max_tool_rounds == 10


@pytest.mark.asyncio
async def test_chatbot_passes_max_tool_rounds_to_agent_loop():
    """Chatbot(max_tool_rounds=N) must propagate to the AgentLoop it builds."""
    bot = Chatbot(default_provider="mock", max_tool_rounds=3, storage="memory")
    assert bot.max_tool_rounds == 3


@pytest.mark.asyncio
async def test_chatbot_default_max_tool_rounds_is_10():
    bot = Chatbot(default_provider="mock", storage="memory")
    assert bot.max_tool_rounds == 10


@pytest.mark.asyncio
async def test_cap_triggers_graceful_wrap_up_call(paginating_tools, ctx):
    """When the cap is hit, the agent must do one more no-tools call and stream text."""
    provider = _InfiniteToolCaller(ProviderConfig(model="test"))
    agent = AgentLoop(provider, paginating_tools, max_tool_rounds=3)

    text_chunks: list[str] = []
    errors: list[str] = []
    tool_results: list[str] = []
    message_ends: list[str | None] = []

    async for event in agent.run([ProviderMessage(role="user", content="page everything")], ctx):
        if isinstance(event, TextDelta):
            text_chunks.append(event.delta)
        elif isinstance(event, ErrorEvent):
            errors.append(event.message)
        elif isinstance(event, ToolResult):
            tool_results.append(event.id)
        elif isinstance(event, MessageEnd):
            message_ends.append(event.finish_reason)

    # Exactly max_tool_rounds tool calls were executed
    assert len(tool_results) == 3
    # The agent did a no-tools wrap-up call
    assert provider.no_tools_call_count == 1
    # The user actually receives the wrap-up text
    assert "".join(text_chunks).strip() == provider.wrap_up_text.strip()
    # No bare ErrorEvent — the wrap-up succeeded
    assert errors == []
    # Final MessageEnd is tagged with the budget reason for observability
    assert message_ends == ["max_tool_rounds"]


@pytest.mark.asyncio
async def test_cap_wrap_up_failure_falls_back_to_error_event(paginating_tools, ctx):
    """If the wrap-up call itself raises, we still emit ErrorEvent + MessageEnd
    rather than swallowing the failure."""

    class _BadWrapUpProvider(_InfiniteToolCaller):
        async def stream(self, messages, *, system_prompt=None, tools_schema=None, model=None):
            if tools_schema is None:
                # Wrap-up call — blow up before any yield to exercise the except branch.
                raise RuntimeError("network down")
            async for chunk in super().stream(
                messages, system_prompt=system_prompt, tools_schema=tools_schema, model=model
            ):
                yield chunk

    provider = _BadWrapUpProvider(ProviderConfig(model="test"))
    agent = AgentLoop(provider, paginating_tools, max_tool_rounds=2)

    errors: list[str] = []
    message_ends: list[str | None] = []
    async for event in agent.run([ProviderMessage(role="user", content="x")], ctx):
        if isinstance(event, ErrorEvent):
            errors.append(event.message)
        if isinstance(event, MessageEnd):
            message_ends.append(event.finish_reason)

    assert any("network down" in e for e in errors)
    assert message_ends == ["max_tool_rounds"]


@pytest.mark.asyncio
async def test_natural_finish_does_not_trigger_wrap_up_path(paginating_tools, ctx):
    """When the model stops on its own (no more tool calls), no wrap-up call happens."""

    class _OneRoundProvider(BaseProvider):
        name = "openai"
        no_tools_calls = 0

        def pydantic_ai_model(self):
            return "t"

        async def stream(self, messages, *, system_prompt=None, tools_schema=None, model=None):
            if tools_schema is None:
                _OneRoundProvider.no_tools_calls += 1
            yield ProviderStreamChunk(text_delta="hello")
            yield ProviderStreamChunk(finish_reason="stop")

    agent = AgentLoop(_OneRoundProvider(ProviderConfig(model="t")), paginating_tools, max_tool_rounds=3)
    async for _ in agent.run([ProviderMessage(role="user", content="hi")], ctx):
        pass

    # Tools are registered so the initial call gets a non-None tools_schema.
    # A wrap-up call would arrive with tools_schema=None — and it must NOT happen
    # when the model finishes naturally without requesting any tool.
    assert _OneRoundProvider.no_tools_calls == 0
