"""Map normalized provider messages to OpenAI Chat Completions JSON."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from chatbot.providers.base import ProviderMessage


def provider_message_to_openai(message: ProviderMessage) -> dict[str, Any]:
    """Build one OpenAI-style chat message dict."""
    out: dict[str, Any] = {"role": message.role}

    if message.role == "tool":
        out["tool_call_id"] = message.tool_call_id or ""
        out["content"] = message.content if message.content is not None else ""
        return out

    if message.tool_calls:
        out["tool_calls"] = message.tool_calls
        out["content"] = message.content
        # Kimi / Moonshot thinking models require this on assistant tool-call turns.
        out["reasoning_content"] = (
            message.reasoning_content if message.reasoning_content is not None else ""
        )
        return out

    out["content"] = message.content if message.content is not None else ""
    return out


def should_include_stream_usage(chat_completions_url: str) -> bool:
    """
    ``stream_options.include_usage`` is not supported on all OpenAI-compatible gateways.

    Set ``OPENAI_STREAM_USAGE=1`` to force on, ``0`` to force off.
    Default: on for ``*.openai.com`` only.
    """
    env = os.environ.get("OPENAI_STREAM_USAGE", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    if env in ("0", "false", "no", "off"):
        return False
    host = (urlparse(chat_completions_url).hostname or "").lower()
    return host.endswith("openai.com")
