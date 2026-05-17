"""Flask adapter — create_blueprint(bot)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from chatbot.core.chatbot import Chatbot, _resolve_user_context
from chatbot.integrations._common import get_protocol_headers, stream_chat_response
from chatbot.protocol.schemas import ChatRequest
from chatbot.protocol.sse import async_to_sync_iter


def create_blueprint(
    bot: Chatbot,
    *,
    user_context: Callable[..., dict[str, Any]] | None = None,
    auth_decorator: Callable[..., Any] | None = None,
    decorators: list[Callable[..., Any]] | None = None,
) -> Any:
    """
    Create a Flask Blueprint for POST /chat (SSE streaming).

    Production: use gunicorn with gevent/eventlet workers for SSE.
    See README for configuration.
    """
    try:
        from flask import Blueprint, Response, request
    except ImportError as exc:
        raise ImportError("Install chatbot[flask] for Flask integration") from exc

    bp = Blueprint("chatbot", __name__)

    def chat_view():
        body = ChatRequest.model_validate(request.get_json())
        ctx: dict[str, Any] | None = None
        if user_context:
            import asyncio

            result = user_context()
            if asyncio.iscoroutine(result):
                loop = asyncio.new_event_loop()
                try:
                    ctx = loop.run_until_complete(_resolve_user_context(user_context))
                finally:
                    loop.close()
            else:
                ctx = result if isinstance(result, dict) else None

        async def generate():
            async for chunk in stream_chat_response(bot, body, ctx):
                yield chunk

        headers = get_protocol_headers()
        return Response(
            async_to_sync_iter(generate()),
            mimetype="text/event-stream",
            headers={**headers, "Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    view = chat_view
    for dec in reversed(decorators or []):
        view = dec(view)
    if auth_decorator:
        view = auth_decorator(view)

    bp.add_url_rule("/chat", view_func=view, methods=["POST"])

    @bp.route("/health", methods=["GET"])
    def health():
        from chatbot.protocol.schemas import PROTOCOL_VERSION

        return {"status": "ok", "protocol": PROTOCOL_VERSION}

    return bp
