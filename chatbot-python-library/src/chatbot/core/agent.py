"""Agent loop — orchestrates LLM streaming, tool calls, and events."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from chatbot.core.context import ToolContext
from chatbot.core.events import (
    ErrorEvent,
    MessageEnd,
    MessageStart,
    StreamEvent,
    TextDelta,
    ThinkingDelta,
    ToolApprovalRequired,
    ToolCallDelta,
    ToolCallEnd,
    ToolCallStart,
    ToolResult,
)
from chatbot.providers.base import BaseProvider, ProviderMessage
from chatbot.tools.registry import ToolRegistry


@dataclass
class _PendingTool:
    id: str
    name: str
    input: dict[str, Any] = field(default_factory=dict)
    input_buffer: str = ""


@dataclass
class _ExecutedTool:
    tool: _PendingTool
    output: Any
    is_error: bool = False


class AgentLoop:
    """
    Agentic loop: stream LLM → detect tool calls → execute tools → continue.
    Uses provider streaming; tool execution via ToolRegistry.
    """

    # When the tool-round budget is exhausted, the agent makes one final
    # no-tools provider call so the model can write a closing answer from
    # whatever it has gathered. This addendum is appended to ``system_prompt``.
    _WRAP_UP_SYSTEM_ADDENDUM = (
        "\n\nIMPORTANT: You have reached the tool-call budget. Do not request any "
        "more tools. Summarize what you have gathered so far and answer the user's "
        "question with the data available. Be explicit if the picture is partial."
    )

    def __init__(
        self,
        provider: BaseProvider,
        tools: ToolRegistry,
        *,
        system_prompt: str | None = None,
        max_tool_rounds: int = 10,
    ) -> None:
        self.provider = provider
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_tool_rounds = max_tool_rounds

    def _tools_schema(self) -> list[dict[str, Any]] | None:
        if not self.tools or not self.tools.list_tools():
            return None
        if getattr(self.provider, "name", None) == "openai":
            return self.tools.to_openai_schema()
        return self.tools.to_anthropic_schema()

    @staticmethod
    def _finalize_tool_input(tool: _PendingTool) -> None:
        if not tool.input_buffer:
            return
        try:
            tool.input = json.loads(tool.input_buffer)
        except json.JSONDecodeError:
            tool.input = {"raw": tool.input_buffer}

    @staticmethod
    def _append_tool_turn(
        messages: list[ProviderMessage],
        *,
        text_buffer: str,
        thinking_buffer: str,
        executed: list[_ExecutedTool],
    ) -> None:
        tool_calls = [
            {
                "id": item.tool.id,
                "type": "function",
                "function": {
                    "name": item.tool.name,
                    "arguments": json.dumps(item.tool.input, ensure_ascii=False),
                },
            }
            for item in executed
        ]
        messages.append(
            ProviderMessage(
                role="assistant",
                content=text_buffer or None,
                tool_calls=tool_calls,
                reasoning_content=thinking_buffer,
            )
        )
        for item in executed:
            if item.is_error:
                payload = {"error": str(item.output)}
            else:
                payload = item.output
            messages.append(
                ProviderMessage(
                    role="tool",
                    tool_call_id=item.tool.id,
                    content=json.dumps(payload, default=str, ensure_ascii=False),
                )
            )

    async def _stream_wrap_up(
        self,
        messages: list[ProviderMessage],
        *,
        model: str | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Final no-tools call so the model produces a closing answer.

        Streams the resulting text/thinking deltas to the caller, then ends with
        ``MessageEnd(finish_reason="max_tool_rounds")`` so observability still
        sees that the budget was hit even though the user got a real answer.
        """
        usage: dict[str, int] | None = None
        wrap_up_system = (self.system_prompt or "") + self._WRAP_UP_SYSTEM_ADDENDUM
        try:
            async for chunk in self.provider.stream(
                messages,
                system_prompt=wrap_up_system,
                tools_schema=None,
                model=model,
            ):
                if chunk.thinking_delta:
                    yield ThinkingDelta(delta=chunk.thinking_delta)
                if chunk.text_delta:
                    yield TextDelta(delta=chunk.text_delta)
                if chunk.finish_reason:
                    usage = chunk.usage
        except Exception as exc:
            # If the wrap-up call itself fails, surface the cap as an error
            # rather than silently dying — same observability as before.
            yield ErrorEvent(
                code="max_tool_rounds",
                message=f"Tool budget exhausted and wrap-up call failed: {exc}",
            )
        yield MessageEnd(usage=usage, finish_reason="max_tool_rounds")

    async def run(
        self,
        messages: list[ProviderMessage],
        ctx: ToolContext,
        *,
        message_id: str | None = None,
        approved_tool_ids: set[str] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[StreamEvent]:
        msg_id = message_id or f"msg_{uuid.uuid4().hex[:12]}"
        yield MessageStart(id=msg_id, role="assistant")

        current_messages = list(messages)
        approved = approved_tool_ids or set()

        for _round in range(self.max_tool_rounds):
            tools_schema = self._tools_schema()
            text_buffer = ""
            thinking_buffer = ""
            pending_tools: dict[str, _PendingTool] = {}
            tool_order: list[str] = []
            finish_reason: str | None = None
            usage: dict[str, int] | None = None

            async for chunk in self.provider.stream(
                current_messages,
                system_prompt=self.system_prompt,
                tools_schema=tools_schema,
                model=model,
            ):
                if chunk.thinking_delta:
                    thinking_buffer += chunk.thinking_delta
                    yield ThinkingDelta(delta=chunk.thinking_delta)

                if chunk.text_delta:
                    text_buffer += chunk.text_delta
                    yield TextDelta(delta=chunk.text_delta)

                if chunk.tool_call_id and chunk.tool_name:
                    tool_id = str(chunk.tool_call_id)
                    if tool_id not in pending_tools:
                        pending_tools[tool_id] = _PendingTool(
                            id=tool_id,
                            name=chunk.tool_name,
                            input=dict(chunk.tool_input or {}),
                        )
                        tool_order.append(tool_id)
                        yield ToolCallStart(
                            id=tool_id,
                            name=chunk.tool_name,
                            input=pending_tools[tool_id].input,
                        )
                    else:
                        pending_tools[tool_id].name = chunk.tool_name

                if chunk.tool_input_delta and chunk.tool_call_id:
                    tool_id = str(chunk.tool_call_id)
                    if tool_id not in pending_tools:
                        pending_tools[tool_id] = _PendingTool(id=tool_id, name="unknown", input={})
                        tool_order.append(tool_id)
                    pending_tools[tool_id].input_buffer += chunk.tool_input_delta
                    yield ToolCallDelta(
                        id=tool_id,
                        input_delta=chunk.tool_input_delta,
                    )

                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
                    usage = chunk.usage

            if not tool_order:
                yield MessageEnd(usage=usage, finish_reason=finish_reason or "stop")
                return

            executed: list[_ExecutedTool] = []
            for tool_id in tool_order:
                tool = pending_tools[tool_id]
                self._finalize_tool_input(tool)

                yield ToolCallEnd(id=tool.id)

                try:
                    result = await self.tools.execute(
                        tool.name,
                        tool.input,
                        ctx,
                        approved=tool.id in approved,
                    )
                except Exception as exc:
                    yield ToolResult(
                        id=tool.id,
                        output={"error": str(exc), "type": type(exc).__name__},
                        is_error=True,
                    )
                    executed.append(_ExecutedTool(tool=tool, output=str(exc), is_error=True))
                    self._append_tool_turn(
                        current_messages,
                        text_buffer=text_buffer,
                        thinking_buffer=thinking_buffer,
                        executed=executed,
                    )
                    text_buffer = ""
                    thinking_buffer = ""
                    break

                if isinstance(result, ToolApprovalRequired):
                    yield ToolApprovalRequired(
                        id=tool.id,
                        name=tool.name,
                        input=tool.input,
                    )
                    pending_idx = tool_order.index(tool_id)
                    for remaining_id in tool_order[pending_idx + 1 :]:
                        yield ToolResult(
                            id=remaining_id,
                            output={"skipped": "Waiting for approval on a previous tool"},
                            is_error=True,
                        )
                    yield MessageEnd(usage=usage, finish_reason="tool_approval_required")
                    return

                yield ToolResult(id=tool.id, output=result, is_error=False)
                executed.append(_ExecutedTool(tool=tool, output=result, is_error=False))

            if executed:
                self._append_tool_turn(
                    current_messages,
                    text_buffer=text_buffer,
                    thinking_buffer=thinking_buffer,
                    executed=executed,
                )
                text_buffer = ""
                thinking_buffer = ""

        # Tool budget exhausted. Instead of leaving the user with no answer,
        # give the model one more chance to summarize — no tools available, so
        # it must respond with text.
        async for event in self._stream_wrap_up(current_messages, model=model):
            yield event
