"""OpenAI provider via httpx streaming API (supports custom base URL and model)."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from chatbot.providers.base import BaseProvider, ProviderMessage, ProviderStreamChunk
from chatbot.providers.openai_messages import (
    provider_message_to_openai,
    should_include_stream_usage,
)
from chatbot.providers.urls import resolve_openai_chat_completions_url

DEFAULT_OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

# Kimi / gateways sometimes send large delta strings; smaller chunks feel smoother in the UI.
_MAX_YIELD_CHARS = 12


@dataclass
class _ToolCallAccum:
    id: str | None = None
    name: str | None = None
    arguments: str = ""
    started: bool = False


@dataclass
class _OpenAIStreamState:
    tool_calls: dict[int, _ToolCallAccum] = field(default_factory=dict)


class OpenAIProvider(BaseProvider):
    name = "openai"

    def pydantic_ai_model(self) -> str:
        return f"openai:{self.config.model}"

    def chat_completions_url(self) -> str:
        return resolve_openai_chat_completions_url(
            self.config.resolve_base_url(default_env="OPENAI_BASE_URL")
        )

    # ----- Override hooks (used by Azure / other OpenAI-compatible subclasses) -----

    def _request_url(self, effective_model: str) -> str:
        """Return the URL to POST the chat-completions request to.

        Subclasses (Azure) may use ``effective_model`` to build a per-deployment URL.
        """
        return self.chat_completions_url()

    def _auth_headers(self) -> dict[str, str]:
        """Return auth + content-type headers. Raises if credentials are missing."""
        api_key = self._resolve_api_key_or_raise()
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _resolve_api_key_or_raise(self) -> str:
        try:
            api_key = self.config.resolve_api_key()
        except ValueError:
            raise
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI provider needs an API key: set providers.openai.api_key, "
                "providers.openai.api_key_env (e.g. OPENAI_API_KEY) with that variable exported, "
                "or export OPENAI_API_KEY in the shell before starting the server."
            )
        return api_key

    # -------------------------------------------------------------------------------

    async def stream(
        self,
        messages: list[ProviderMessage],
        *,
        system_prompt: str | None = None,
        tools_schema: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        headers = self._auth_headers()

        openai_messages: list[dict[str, Any]] = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        openai_messages.extend(provider_message_to_openai(m) for m in messages)

        effective_model = self.effective_model(model)
        url = self._request_url(effective_model)
        body: dict[str, Any] = {
            "model": effective_model,
            "messages": openai_messages,
            "stream": True,
        }
        if should_include_stream_usage(url):
            body["stream_options"] = {"include_usage": True}
        if tools_schema:
            body["tools"] = [{"type": "function", "function": t} for t in tools_schema]

        state = _OpenAIStreamState()

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=body, headers=headers) as response:
                if response.is_error:
                    detail = (await response.aread()).decode("utf-8", errors="replace").strip()
                    raise httpx.HTTPStatusError(
                        _format_openai_http_error(response.status_code, url, detail),
                        request=response.request,
                        response=response,
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]" or not raw:
                        continue
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    for chunk in _parse_openai_payload(payload, state):
                        yield chunk


def _format_openai_http_error(status_code: int, url: str, detail: str) -> str:
    hint = ""
    if status_code == 400 and "stream_options" in detail:
        hint = " Try OPENAI_STREAM_USAGE=0 in .env."
    elif status_code == 400:
        hint = " Check model name, message format, and tool payloads."
    base = f"LLM API returned HTTP {status_code} for {url}"
    if detail:
        return f"{base}: {detail[:1500]}{hint}"
    return f"{base} (empty response body).{hint}"


def _smooth_text_chunks(text: str, *, thinking: bool = False) -> Iterator[ProviderStreamChunk]:
    """Split large provider deltas so the UI can animate token-by-token."""
    if not text:
        return
    field = "thinking_delta" if thinking else "text_delta"
    if len(text) <= _MAX_YIELD_CHARS:
        yield ProviderStreamChunk(**{field: text})
        return
    step = 4 if thinking else 3
    for i in range(0, len(text), step):
        piece = text[i : i + step]
        yield ProviderStreamChunk(**{field: piece})


def _parse_openai_payload(
    data: dict[str, Any],
    state: _OpenAIStreamState,
) -> list[ProviderStreamChunk]:
    out: list[ProviderStreamChunk] = []

    usage = data.get("usage")
    choices = data.get("choices") or []
    if not choices:
        if usage:
            out.append(
                ProviderStreamChunk(
                    finish_reason="stop",
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                )
            )
        return out

    choice = choices[0]
    delta = choice.get("delta") or {}
    finish = choice.get("finish_reason")

    reasoning = delta.get("reasoning_content") or delta.get("reasoning")
    if reasoning:
        out.extend(_smooth_text_chunks(str(reasoning), thinking=True))

    content = delta.get("content")
    if content:
        out.extend(_smooth_text_chunks(str(content), thinking=False))

    tool_calls = delta.get("tool_calls")
    if tool_calls:
        out.extend(_parse_tool_call_deltas(tool_calls, state))

    if finish:
        usage = data.get("usage") or {}
        out.append(
            ProviderStreamChunk(
                finish_reason=finish,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            )
        )
    return out


def _parse_tool_call_deltas(
    tool_calls: list[dict[str, Any]],
    state: _OpenAIStreamState,
) -> list[ProviderStreamChunk]:
    out: list[ProviderStreamChunk] = []
    for tc in tool_calls:
        index = int(tc.get("index", 0))
        acc = state.tool_calls.setdefault(index, _ToolCallAccum())
        if tc.get("id"):
            acc.id = tc["id"]
        fn = tc.get("function") or {}
        if fn.get("name"):
            acc.name = fn["name"]
        if fn.get("arguments"):
            acc.arguments += fn["arguments"]

        if acc.id and acc.name and not acc.started:
            acc.started = True
            out.append(
                ProviderStreamChunk(
                    tool_call_id=acc.id,
                    tool_name=acc.name,
                    tool_input={},
                )
            )

        if fn.get("arguments") and acc.id:
            out.append(
                ProviderStreamChunk(
                    tool_call_id=acc.id,
                    tool_input_delta=fn["arguments"],
                )
            )
    return out
