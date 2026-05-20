"""Tests for SSE encoding/decoding (protocol.sse)."""
from __future__ import annotations

import json

import pytest

from chatbot.core.events import MessageStart, TextDelta
from chatbot.protocol.sse import (
    SSEDecoder,
    encode_sse_event,
    sse_stream,
    stream_event_to_sse,
)


# ─────────────────────────────────────────────────────────────────────────────
# encode_sse_event
# ─────────────────────────────────────────────────────────────────────────────

def test_encode_sse_event_basic_shape() -> None:
    out = encode_sse_event("text_delta", {"delta": "hi"})
    # Must be: event line + data line + blank line terminator.
    assert out == 'event: text_delta\ndata: {"delta": "hi"}\n\n'


def test_encode_sse_event_empty_data_becomes_object() -> None:
    out = encode_sse_event("done")
    assert out == "event: done\ndata: {}\n\n"


def test_encode_sse_event_preserves_unicode() -> None:
    out = encode_sse_event("text_delta", {"delta": "héllo · 🌍"})
    # ensure_ascii=False is set, so the payload is preserved verbatim.
    assert "héllo · 🌍" in out


# ─────────────────────────────────────────────────────────────────────────────
# stream_event_to_sse
# ─────────────────────────────────────────────────────────────────────────────

def test_stream_event_to_sse_uses_event_type_and_payload() -> None:
    out = stream_event_to_sse(MessageStart(id="m_1", role="assistant"))
    assert out.startswith("event: message_start\n")
    assert '"id": "m_1"' in out
    assert '"role": "assistant"' in out


# ─────────────────────────────────────────────────────────────────────────────
# sse_stream: async iterator wraps events, emits done at the end
# ─────────────────────────────────────────────────────────────────────────────

async def test_sse_stream_emits_done_after_events() -> None:
    async def source():
        yield TextDelta(delta="a")
        yield TextDelta(delta="b")

    chunks = [c async for c in sse_stream(source())]
    # Two text_delta frames + a terminal done.
    assert any("text_delta" in c and '"a"' in c for c in chunks)
    assert any("text_delta" in c and '"b"' in c for c in chunks)
    assert chunks[-1].startswith("event: done\n")


async def test_sse_stream_catches_upstream_exception_and_emits_error_then_done() -> None:
    async def boom():
        yield TextDelta(delta="ok")
        raise RuntimeError("upstream failed")

    chunks = [c async for c in sse_stream(boom())]
    # The error frame appears before done.
    error_idx = next(i for i, c in enumerate(chunks) if c.startswith("event: error"))
    done_idx = next(i for i, c in enumerate(chunks) if c.startswith("event: done"))
    assert error_idx < done_idx
    # The error message is propagated to the client.
    assert "upstream failed" in chunks[error_idx]


# ─────────────────────────────────────────────────────────────────────────────
# SSEDecoder (client-side helper)
# ─────────────────────────────────────────────────────────────────────────────

def test_decoder_parses_a_single_complete_frame() -> None:
    decoder = SSEDecoder()
    events = decoder.feed("event: text_delta\ndata: {\"delta\": \"hi\"}\n\n")
    assert events == [("text_delta", {"delta": "hi"})]


def test_decoder_buffers_partial_frames_across_chunks() -> None:
    decoder = SSEDecoder()
    # Split a frame across two feeds.
    assert decoder.feed("event: text_delta\ndata: ") == []
    events = decoder.feed("{\"delta\": \"hi\"}\n\n")
    assert events == [("text_delta", {"delta": "hi"})]


def test_decoder_parses_multiple_frames_in_one_chunk() -> None:
    decoder = SSEDecoder()
    blob = (
        "event: text_delta\n"
        'data: {"delta": "a"}\n\n'
        "event: text_delta\n"
        'data: {"delta": "b"}\n\n'
    )
    events = decoder.feed(blob)
    assert events == [
        ("text_delta", {"delta": "a"}),
        ("text_delta", {"delta": "b"}),
    ]
