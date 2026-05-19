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
        # Kimi / Moonshot thinking models require this on assistant tool-call turns,
        # but most providers (e.g. Mistral) reject it as an extra field — only include
        # it when there is actual reasoning content to send.
        if message.reasoning_content:
            out["reasoning_content"] = message.reasoning_content
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
    # Native OpenAI and Azure OpenAI both support stream_options.include_usage
    # on recent API versions. Other gateways often don't and 400 on it.
    return host.endswith("openai.com") or host.endswith("openai.azure.com")
