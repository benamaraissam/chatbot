"""Anthropic (Claude) provider via httpx streaming API."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from chatbot.providers.base import BaseProvider, ProviderConfig, ProviderMessage, ProviderStreamChunk
from chatbot.providers.urls import resolve_anthropic_messages_url

DEFAULT_ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def pydantic_ai_model(self) -> str:
        return f"anthropic:{self.config.model}"

    def messages_url(self) -> str:
        return resolve_anthropic_messages_url(
            self.config.resolve_base_url(default_env="ANTHROPIC_BASE_URL")
        )

    async def stream(
        self,
        messages: list[ProviderMessage],
        *,
        system_prompt: str | None = None,
        tools_schema: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        api_key = self.config.resolve_api_key() or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")

        anthropic_messages = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        body: dict[str, Any] = {
            "model": self.effective_model(model),
            "max_tokens": 4096,
            "messages": anthropic_messages,
            "stream": True,
        }
        if system_prompt:
            body["system"] = system_prompt
        if tools_schema:
            body["tools"] = tools_schema

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", self.messages_url(), json=body, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]" or not raw:
                        continue
                    event = json.loads(raw)
                    chunk = _parse_anthropic_event(event)
                    if chunk:
                        yield chunk


def _parse_anthropic_event(event: dict[str, Any]) -> ProviderStreamChunk | None:
    event_type = event.get("type")
    match event_type:
        case "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return ProviderStreamChunk(text_delta=delta.get("text", ""))
            if delta.get("type") == "input_json_delta":
                return ProviderStreamChunk(
                    tool_call_id=event.get("index"),
                    tool_input_delta=delta.get("partial_json", ""),
                )
        case "message_delta":
            usage = event.get("usage")
            return ProviderStreamChunk(
                finish_reason=event.get("delta", {}).get("stop_reason", "stop"),
                usage={
                    "prompt_tokens": usage.get("input_tokens", 0) if usage else 0,
                    "completion_tokens": usage.get("output_tokens", 0) if usage else 0,
                    "total_tokens": (
                        (usage.get("input_tokens", 0) + usage.get("output_tokens", 0)) if usage else 0
                    ),
                },
            )
        case "content_block_start":
            block = event.get("content_block", {})
            if block.get("type") == "tool_use":
                return ProviderStreamChunk(
                    tool_call_id=block.get("id"),
                    tool_name=block.get("name"),
                    tool_input={},
                )
    return None
