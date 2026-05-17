"""Django adapter — chatbot_urls(bot)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from chatbot.core.chatbot import Chatbot, _resolve_user_context
from chatbot.integrations._common import get_protocol_headers, stream_chat_response
from chatbot.protocol.schemas import ChatRequest, PROTOCOL_VERSION


def chatbot_urls(
    bot: Chatbot,
    *,
    user_context: Callable[..., dict[str, Any]] | None = None,
) -> list[Any]:
    """
    Return Django urlpatterns for the chatbot API.

    Usage:
        urlpatterns = [path("api/chat/", include(chatbot_urls(bot, user_context=get_user)))]
    """
    try:
        from django.http import JsonResponse, StreamingHttpResponse
        from django.urls import path
        from django.views.decorators.csrf import csrf_exempt
        from django.views.decorators.http import require_http_methods
    except ImportError as exc:
        raise ImportError("Install chatbot[django] for Django integration") from exc

    import asyncio
    import json

    @csrf_exempt
    @require_http_methods(["POST"])
    async def chat_view(request):
        body = ChatRequest.model_validate(json.loads(request.body))
        ctx = None
        if user_context:
            ctx = await _resolve_user_context(user_context, request=request)

        async def generate():
            async for chunk in stream_chat_response(bot, body, ctx):
                yield chunk.encode("utf-8")

        response = StreamingHttpResponse(generate(), content_type="text/event-stream")
        for key, value in get_protocol_headers().items():
            response[key] = value
        response["Cache-Control"] = "no-cache"
        return response

    def health_view(request):
        return JsonResponse({"status": "ok", "protocol": PROTOCOL_VERSION})

    return [
        path("chat", chat_view, name="chatbot-chat"),
        path("health", health_view, name="chatbot-health"),
    ]
