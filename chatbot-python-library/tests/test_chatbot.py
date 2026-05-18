"""Chatbot core integration tests."""

import pytest

from chatbot import Chatbot, TextDelta
from chatbot.protocol.schemas import ChatRequest, Message, TextPart


@pytest.fixture
def bot():
    return Chatbot(default_provider="mock", storage="memory")


@pytest.mark.asyncio
async def test_send_mock(bot):
    response = await bot.send("Hello world", user_context={"user_id": "u1"})
    assert "Hello world" in response.text
    assert "Hi!" in response.text or "[mock]" in response.text


@pytest.mark.asyncio
async def test_stream_mock(bot):
    deltas = []
    async for event in bot.stream("Hi there"):
        if isinstance(event, TextDelta):
            deltas.append(event.delta)
    assert len(deltas) > 0
    joined = "".join(deltas)
    assert "Hi!" in joined or "[mock]" in joined


@pytest.mark.asyncio
async def test_conversation_multi_turn(bot):
    conv = bot.conversation(user_context={"user_id": "u2"})
    r1 = await conv.send("First message")
    r2 = await conv.send("Second message")
    assert r1.conversation_id == conv.id
    assert r2.conversation_id == conv.id


@pytest.mark.asyncio
async def test_handle_request(bot):
    request = ChatRequest(
        messages=[
            Message(id="m1", role="user", parts=[TextPart(text="Protocol test")]),
        ],
        conversationId="conv_test",
    )
    events = []
    async for event in bot.handle_request(request, {"user_id": "u3"}):
        events.append(event)
    types = [e.event_type for e in events]
    assert "message_start" in types
    assert "text_delta" in types
    assert "done" in types


@pytest.mark.asyncio
async def test_storage_persistence():
    bot = Chatbot(default_provider="mock", storage="memory")
    conv_id = "conv_persist"
    await bot.send("Remember this", conversation_id=conv_id)
    history = await bot._storage.get_messages(conv_id)
    assert len(history) >= 2  # user + assistant
