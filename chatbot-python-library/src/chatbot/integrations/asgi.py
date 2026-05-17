"""ASGI application factory — framework-agnostic HTTP entry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from chatbot.core.chatbot import Chatbot


def create_asgi_app(
    bot: Chatbot,
    *,
    user_context: Callable[..., dict[str, Any]] | None = None,
    path_prefix: str = "",
) -> Any:
    """
    Create a standalone ASGI app using Starlette routes.

    Usage:
        app = create_asgi_app(bot)
        uvicorn.run(app, host="0.0.0.0", port=8000)
    """
    try:
        from starlette.applications import Starlette
        from starlette.routing import Mount
    except ImportError as exc:
        raise ImportError("Install chatbot[starlette] for ASGI integration") from exc

    from chatbot.integrations.starlette import create_routes

    routes = create_routes(bot, user_context=user_context)
    prefix = path_prefix.rstrip("/")
    if prefix:
        return Starlette(routes=[Mount(prefix, routes=routes)])
    return Starlette(routes=routes)
