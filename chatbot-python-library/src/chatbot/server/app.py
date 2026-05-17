"""Standalone FastAPI server application."""

from __future__ import annotations

from chatbot import Chatbot
from chatbot.server.config import ServerConfig


def create_app(config: ServerConfig | None = None):
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:
        raise ImportError("Install chatbot[server] for standalone server") from exc

    from chatbot.integrations.fastapi import create_router

    cfg = config or ServerConfig()
    providers = {name: p.model_dump() for name, p in cfg.providers.items()}

    bot = Chatbot(
        providers=providers,
        default_provider=cfg.default_provider,
        system_prompt=cfg.system_prompt,
        storage=cfg.storage,
    )

    app = FastAPI(title="Chatbot Server", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_router(bot), prefix="/api/chat", tags=["chatbot"])
    app.state.chatbot = bot
    return app
