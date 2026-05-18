"""URL normalization for OpenAI-compatible and Anthropic API endpoints."""

from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse


def resolve_openai_chat_completions_url(
    base_url: str | None,
    *,
    default: str = "https://api.openai.com/v1/chat/completions",
    env_var: str = "OPENAI_BASE_URL",
) -> str:
    """
    Resolve the chat completions endpoint URL.

    Accepts:
    - Full URL: ``https://gateway.example.com/v1/chat/completions``
    - API root: ``https://gateway.example.com/v1`` or ``https://gateway.example.com/v1/``
    - Host only: ``https://gateway.example.com`` → ``/v1/chat/completions``

    Falls back to ``OPENAI_BASE_URL`` env var when ``base_url`` is omitted.
    """
    raw = (base_url or os.environ.get(env_var) or "").strip().rstrip("/")
    if not raw:
        return default

    if raw.endswith("/chat/completions"):
        return raw

    parsed = urlparse(raw)
    path = parsed.path.rstrip("/")

    if path.endswith("/v1"):
        new_path = f"{path}/chat/completions"
    elif path in ("", "/"):
        new_path = "/v1/chat/completions"
    else:
        new_path = f"{path}/chat/completions"

    return urlunparse(parsed._replace(path=new_path))


def resolve_anthropic_messages_url(
    base_url: str | None,
    *,
    default: str = "https://api.anthropic.com/v1/messages",
    env_var: str = "ANTHROPIC_BASE_URL",
) -> str:
    """Resolve Anthropic messages endpoint (same path rules as OpenAI-style roots)."""
    raw = (base_url or os.environ.get(env_var) or "").strip().rstrip("/")
    if not raw:
        return default

    if raw.endswith("/messages"):
        return raw

    parsed = urlparse(raw)
    path = parsed.path.rstrip("/")

    if path.endswith("/v1"):
        new_path = f"{path}/messages"
    elif path in ("", "/"):
        new_path = "/v1/messages"
    else:
        new_path = f"{path}/messages"

    return urlunparse(parsed._replace(path=new_path))
