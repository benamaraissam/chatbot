"""Shared helpers for framework adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from chatbot.core.chatbot import Chatbot
from chatbot.protocol.schemas import ChatRequest, PROTOCOL_VERSION
from chatbot.protocol.sse import sse_stream

PROTOCOL_HEADER = "X-Chatbot-Protocol-Version"


async def stream_chat_response(
    bot: Chatbot,
    request: ChatRequest,
    user_context: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    events = bot.handle_request(request, user_context)
    async for chunk in sse_stream(events):
        yield chunk


def get_protocol_headers() -> dict[str, str]:
    return {PROTOCOL_HEADER: PROTOCOL_VERSION}
