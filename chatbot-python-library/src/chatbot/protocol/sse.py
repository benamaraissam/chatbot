"""Server-Sent Events encoding/decoding for the chatbot protocol."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

from chatbot.core.events import StreamEvent


class _ChatbotJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles Pydantic models (e.g. FilePart returned by tools)."""

    def default(self, obj: Any) -> Any:
        # Pydantic v2 models expose model_dump(); use by_alias=True so camelCase
        # field aliases (mimeType etc.) round-trip correctly to the frontend.
        if hasattr(obj, "model_dump"):
            return obj.model_dump(by_alias=True)
        # Pydantic v1 models expose dict()
        if hasattr(obj, "dict"):
            return obj.dict()
        return super().default(obj)


def encode_sse_event(event_type: str, data: dict[str, Any] | None = None) -> str:
    """Encode a single SSE frame."""
    payload = json.dumps(data or {}, ensure_ascii=False, cls=_ChatbotJSONEncoder)
    return f"event: {event_type}\ndata: {payload}\n\n"


def stream_event_to_sse(event: StreamEvent) -> str:
    """Convert a StreamEvent to an SSE string."""
    return encode_sse_event(event.event_type, event.to_payload())


async def sse_stream(events: AsyncIterator[StreamEvent]) -> AsyncIterator[str]:
    """Async iterator of SSE-encoded strings from stream events.

    Exceptions raised by the upstream iterator are caught and forwarded to the
    client as an ``error`` SSE frame so the HTTP response always terminates with
    a complete chunked-encoding sequence (avoiding ERR_INCOMPLETE_CHUNKED_ENCODING).
    """
    try:
        async for event in events:
            yield stream_event_to_sse(event)
    except Exception as exc:  # noqa: BLE001
        yield encode_sse_event("error", {"message": str(exc)})
    finally:
        yield encode_sse_event("done", {})


class SSEDecoder:
    """Decode SSE frames from a text buffer (client-side helper)."""

    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, chunk: str) -> list[tuple[str, dict[str, Any]]]:
        self._buffer += chunk
        frames: list[tuple[str, dict[str, Any]]] = []
        while "\n\n" in self._buffer:
            block, self._buffer = self._buffer.split("\n\n", 1)
            event_type, data = _parse_sse_block(block)
            if event_type:
                frames.append((event_type, data))
        return frames


def _parse_sse_block(block: str) -> tuple[str | None, dict[str, Any]]:
    event_type: str | None = None
    data: dict[str, Any] = {}
    for line in block.strip().split("\n"):
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            raw = line[5:].strip()
            data = json.loads(raw) if raw else {}
    return event_type, data


def async_to_sync_iter(async_iter: AsyncIterator[str]) -> Iterator[str]:
    """Bridge async SSE iterator for sync frameworks (Flask)."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:

        async def _collect() -> list[str]:
            return [chunk async for chunk in async_iter]

        return iter(loop.run_until_complete(_collect()))
    finally:
        loop.close()
