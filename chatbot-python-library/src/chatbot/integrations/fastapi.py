"""FastAPI adapter — create_router(bot)."""

from collections.abc import Callable
from typing import Any

from chatbot.core.chatbot import Chatbot, _resolve_user_context
from chatbot.core.context import UserContextProvider
from chatbot.integrations._common import get_protocol_headers, stream_chat_response
from chatbot.protocol.schemas import PROTOCOL_VERSION, ChatRequest


def create_router(
    bot: Chatbot,
    *,
    user_context: UserContextProvider | Callable[..., dict[str, Any]] | None = None,
    auth: Callable[..., Any] | None = None,
) -> Any:
    """
    Create a FastAPI APIRouter for POST /chat (SSE streaming).

    Usage:
        app.include_router(create_router(bot, user_context=get_user), prefix="/api/chat")
    """
    try:
        from fastapi import APIRouter, Depends, Request
        from fastapi.responses import StreamingResponse
    except ImportError as exc:
        raise ImportError("Install chatbot[fastapi] for FastAPI integration") from exc

    router = APIRouter()
    dependencies = [Depends(auth)] if auth else []

    @router.post("/chat", dependencies=dependencies)
    async def chat_endpoint(body: ChatRequest, http_request: Request) -> StreamingResponse:
        ctx = (
            await _resolve_user_context(user_context, request=http_request)
            if user_context
            else None
        )

        async def event_generator():
            async for chunk in stream_chat_response(bot, body, ctx):
                yield chunk

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                **get_protocol_headers(),
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @router.get("/health")
    async def health():
        return {"status": "ok", "protocol": PROTOCOL_VERSION}

    return router
