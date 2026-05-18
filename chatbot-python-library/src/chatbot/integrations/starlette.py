"""Starlette adapter."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from chatbot.core.chatbot import Chatbot, _resolve_user_context
from chatbot.integrations._common import get_protocol_headers, stream_chat_response
from chatbot.protocol.schemas import PROTOCOL_VERSION, ChatRequest


def create_routes(
    bot: Chatbot,
    *,
    user_context: Callable[..., dict[str, Any]] | None = None,
) -> list[Any]:
    try:
        from starlette.requests import Request
        from starlette.responses import JSONResponse, StreamingResponse
        from starlette.routing import Route
    except ImportError as exc:
        raise ImportError("Install chatbot[starlette] for Starlette integration") from exc

    async def chat_endpoint(request: Request):
        body = ChatRequest.model_validate(await request.json())
        ctx = await _resolve_user_context(user_context, request=request) if user_context else None

        async def event_generator():
            async for chunk in stream_chat_response(bot, body, ctx):
                yield chunk

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={**get_protocol_headers(), "Cache-Control": "no-cache"},
        )

    async def health(_request: Request):
        return JSONResponse({"status": "ok", "protocol": PROTOCOL_VERSION})

    return [
        Route("/chat", chat_endpoint, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
    ]
