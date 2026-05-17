"""Streaming event types for library mode and SSE adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class StreamEvent:
    """Base streaming event emitted by Chatbot.stream()."""

    event_type: str

    def to_payload(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class MessageStart(StreamEvent):
    event_type: Literal["message_start"] = field(default="message_start", init=False)
    id: str = ""
    role: str = "assistant"

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "role": self.role}


@dataclass(frozen=True)
class TextDelta(StreamEvent):
    event_type: Literal["text_delta"] = field(default="text_delta", init=False)
    delta: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {"delta": self.delta}


@dataclass(frozen=True)
class ThinkingDelta(StreamEvent):
    """Streamed internal reasoning / thinking (shown separately from the answer)."""

    event_type: Literal["thinking_delta"] = field(default="thinking_delta", init=False)
    delta: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {"delta": self.delta}


@dataclass(frozen=True)
class ToolCallStart(StreamEvent):
    event_type: Literal["tool_call_start"] = field(default="tool_call_start", init=False)
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "input": self.input}


@dataclass(frozen=True)
class ToolCallDelta(StreamEvent):
    event_type: Literal["tool_call_delta"] = field(default="tool_call_delta", init=False)
    id: str = ""
    input_delta: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "inputDelta": self.input_delta}


@dataclass(frozen=True)
class ToolCallEnd(StreamEvent):
    event_type: Literal["tool_call_end"] = field(default="tool_call_end", init=False)
    id: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id}


@dataclass(frozen=True)
class ToolResult(StreamEvent):
    event_type: Literal["tool_result"] = field(default="tool_result", init=False)
    id: str = ""
    output: Any = None
    is_error: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "output": self.output, "isError": self.is_error}


@dataclass(frozen=True)
class ToolApprovalRequired(StreamEvent):
    event_type: Literal["tool_approval_required"] = field(
        default="tool_approval_required", init=False
    )
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "input": self.input}


@dataclass(frozen=True)
class MessageEnd(StreamEvent):
    event_type: Literal["message_end"] = field(default="message_end", init=False)
    usage: dict[str, int] | None = None
    finish_reason: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.usage is not None:
            payload["usage"] = self.usage
        if self.finish_reason is not None:
            payload["finishReason"] = self.finish_reason
        return payload


@dataclass(frozen=True)
class ErrorEvent(StreamEvent):
    event_type: Literal["error"] = field(default="error", init=False)
    code: str = "internal_error"
    message: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class Done(StreamEvent):
    event_type: Literal["done"] = field(default="done", init=False)

    def to_payload(self) -> dict[str, Any]:
        return {}


def event_from_type(event_type: str, payload: dict[str, Any]) -> StreamEvent:
    """Reconstruct a StreamEvent from SSE payload (testing/helper)."""
    match event_type:
        case "message_start":
            return MessageStart(id=payload.get("id", ""), role=payload.get("role", "assistant"))
        case "text_delta":
            return TextDelta(delta=payload.get("delta", ""))
        case "thinking_delta":
            return ThinkingDelta(delta=payload.get("delta", ""))
        case "tool_call_start":
            return ToolCallStart(
                id=payload.get("id", ""),
                name=payload.get("name", ""),
                input=payload.get("input", {}),
            )
        case "tool_call_delta":
            return ToolCallDelta(id=payload.get("id", ""), input_delta=payload.get("inputDelta", ""))
        case "tool_call_end":
            return ToolCallEnd(id=payload.get("id", ""))
        case "tool_result":
            return ToolResult(
                id=payload.get("id", ""),
                output=payload.get("output"),
                is_error=payload.get("isError", False),
            )
        case "tool_approval_required":
            return ToolApprovalRequired(
                id=payload.get("id", ""),
                name=payload.get("name", ""),
                input=payload.get("input", {}),
            )
        case "message_end":
            return MessageEnd(
                usage=payload.get("usage"),
                finish_reason=payload.get("finishReason"),
            )
        case "error":
            return ErrorEvent(code=payload.get("code", "error"), message=payload.get("message", ""))
        case "done":
            return Done()
        case _:
            return ErrorEvent(code="unknown_event", message=f"Unknown event: {event_type}")
