"""Protocol schema and SSE tests."""

import json

import pytest

from chatbot.protocol.schemas import PROTOCOL_VERSION, ChatRequest, ImagePart, Message, TextPart
from chatbot.protocol.sse import SSEDecoder, encode_sse_event, stream_event_to_sse
from chatbot.core.events import TextDelta, ThinkingDelta, event_from_type


def test_protocol_version():
    assert PROTOCOL_VERSION == "1"


def test_chat_request_image_part():
    raw = {
        "messages": [
            {
                "id": "m1",
                "role": "user",
                "parts": [
                    {"type": "text", "text": "Describe"},
                    {"type": "image", "mimeType": "image/png", "data": "abc", "name": "x.png"},
                ],
            }
        ],
    }
    req = ChatRequest.model_validate(raw)
    part = req.messages[0].parts[1]
    assert isinstance(part, ImagePart)
    assert part.mime_type == "image/png"


def test_chat_request_aliases():
    raw = {
        "messages": [{"id": "m1", "role": "user", "parts": [{"type": "text", "text": "Hi"}]}],
        "conversationId": "conv_1",
        "model": "mock",
        "metadata": {"userId": "u1"},
    }
    req = ChatRequest.model_validate(raw)
    assert req.conversation_id == "conv_1"
    assert req.messages[0].parts[0].text == "Hi"


def test_encode_sse_event():
    frame = encode_sse_event("text_delta", {"delta": "Hello"})
    assert "event: text_delta" in frame
    assert '"delta": "Hello"' in frame or '"delta":"Hello"' in frame.replace(" ", "")


def test_sse_decoder():
    decoder = SSEDecoder()
    frame = encode_sse_event("text_delta", {"delta": "x"})
    events = decoder.feed(frame)
    assert len(events) == 1
    assert events[0][0] == "text_delta"
    assert events[0][1]["delta"] == "x"


def test_event_from_type():
    e = event_from_type("text_delta", {"delta": "hi"})
    assert isinstance(e, TextDelta)
    assert e.delta == "hi"

    t = event_from_type("thinking_delta", {"delta": "reasoning"})
    assert isinstance(t, ThinkingDelta)
    assert t.delta == "reasoning"


@pytest.mark.asyncio
async def test_sse_stream():
    from chatbot.core.events import Done, MessageStart, TextDelta
    from chatbot.protocol.sse import sse_stream

    async def events():
        yield MessageStart(id="m1", role="assistant")
        yield TextDelta(delta="Hi")
        yield Done()

    chunks = [c async for c in sse_stream(events())]
    assert any("text_delta" in c for c in chunks)
    assert any("done" in c for c in chunks)
