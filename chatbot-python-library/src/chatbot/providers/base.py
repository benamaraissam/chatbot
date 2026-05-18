"""LLM provider abstraction."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""

    model: str
    api_key_env: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    base_url_env: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def resolve_api_key(self) -> str | None:
        if self.api_key:
            return self.api_key
        if self.api_key_env:
            key = os.environ.get(self.api_key_env)
            if key:
                return key
            if self.api_key_env.startswith(("sk-", "pk-", "rk-")) or len(self.api_key_env) > 40:
                raise ValueError(
                    "Provider config: api_key_env must be the NAME of an environment variable "
                    "(e.g. OPENAI_API_KEY), not the secret key itself. "
                    "Use api_key='...' in config, or run: export OPENAI_API_KEY='your-key'"
                )
        return None

    def resolve_base_url(self, default_env: str | None = None) -> str | None:
        if self.base_url:
            return self.base_url
        if self.base_url_env:
            return os.environ.get(self.base_url_env)
        if default_env:
            return os.environ.get(default_env)
        return None


@dataclass
class ProviderMessage:
    role: str
    content: str | list[dict[str, Any]] | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    reasoning_content: str | None = None


@dataclass
class ProviderStreamChunk:
    """Normalized chunk from any provider."""

    text_delta: str | None = None
    thinking_delta: str | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_input_delta: str | None = None
    tool_input: dict[str, Any] | None = None
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class BaseProvider(ABC):
    """Abstract LLM provider with streaming support."""

    name: str

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    def pydantic_ai_model(self) -> str:
        """Return pydantic-ai model identifier string."""

    @abstractmethod
    async def stream(
        self,
        messages: list[ProviderMessage],
        *,
        system_prompt: str | None = None,
        tools_schema: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        """Stream normalized chunks from the LLM."""

    def effective_model(self, model_override: str | None = None) -> str:
        return model_override or self.config.model


class ProviderRegistry:
    """Registry of named providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> BaseProvider:
        if name not in self._providers:
            raise KeyError(f"Unknown provider: {name}. Available: {list(self._providers)}")
        return self._providers[name]

    @property
    def names(self) -> list[str]:
        return list(self._providers.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._providers


def build_default_registry(
    configs: dict[str, ProviderConfig | dict[str, Any]],
) -> ProviderRegistry:
    """Build registry from Chatbot-style provider config dict."""
    from chatbot.providers.anthropic import AnthropicProvider
    from chatbot.providers.litellm import LiteLLMProvider
    from chatbot.providers.mock import MockProvider
    from chatbot.providers.openai import OpenAIProvider

    registry = ProviderRegistry()
    factory_map: dict[str, type[BaseProvider]] = {
        "mock": MockProvider,
        "claude": AnthropicProvider,
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gpt": OpenAIProvider,
        "litellm": LiteLLMProvider,
    }

    for name, raw in configs.items():
        cfg = raw if isinstance(raw, ProviderConfig) else ProviderConfig(**raw)
        cls = factory_map.get(name, AnthropicProvider if "claude" in cfg.model else OpenAIProvider)
        if name == "mock" or cfg.model == "mock":
            cls = MockProvider
        registry.register(name, cls(cfg))
    return registry
