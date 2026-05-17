"""LiteLLM provider for 100+ model backends."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from chatbot.providers.base import BaseProvider, ProviderConfig, ProviderMessage, ProviderStreamChunk


class LiteLLMProvider(BaseProvider):
    name = "litellm"

    def pydantic_ai_model(self) -> str:
        return self.config.model

    async def stream(
        self,
        messages: list[ProviderMessage],
        *,
        system_prompt: str | None = None,
        tools_schema: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        try:
            import litellm
        except ImportError as exc:
            raise ImportError("Install chatbot[litellm] to use LiteLLM provider") from exc

        litellm_messages: list[dict[str, str]] = []
        if system_prompt:
            litellm_messages.append({"role": "system", "content": system_prompt})
        litellm_messages.extend({"role": m.role, "content": m.content} for m in messages)

        api_key = self.config.resolve_api_key()
        kwargs: dict[str, Any] = {
            "model": self.effective_model(model),
            "messages": litellm_messages,
            "stream": True,
        }
        if api_key:
            kwargs["api_key"] = api_key
        base = self.config.resolve_base_url()
        if base:
            kwargs["api_base"] = base.rstrip("/")

        response = await litellm.acompletion(**kwargs)
        async for chunk in response:
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None):
                yield ProviderStreamChunk(text_delta=delta.content)
            finish = chunk.choices[0].finish_reason
            if finish:
                usage = getattr(chunk, "usage", None)
                usage_dict = None
                if usage:
                    usage_dict = {
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage, "completion_tokens", 0),
                        "total_tokens": getattr(usage, "total_tokens", 0),
                    }
                yield ProviderStreamChunk(finish_reason=finish, usage=usage_dict)
