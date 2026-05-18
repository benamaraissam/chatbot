"""Provider URL normalization and model override tests."""

import pytest

from chatbot import Chatbot
from chatbot.providers.openai import OpenAIProvider
from chatbot.providers.urls import (
    resolve_anthropic_messages_url,
    resolve_openai_chat_completions_url,
)
from chatbot.providers.base import ProviderConfig


def test_resolve_openai_full_url():
    url = "https://gateway.example.com/v1/chat/completions"
    assert resolve_openai_chat_completions_url(url) == url


def test_resolve_openai_v1_root():
    assert (
        resolve_openai_chat_completions_url("https://gateway.example.com/v1")
        == "https://gateway.example.com/v1/chat/completions"
    )


def test_resolve_openai_host_only():
    assert (
        resolve_openai_chat_completions_url("https://gateway.example.com")
        == "https://gateway.example.com/v1/chat/completions"
    )


def test_resolve_openai_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    assert (
        resolve_openai_chat_completions_url(None)
        == "http://localhost:11434/v1/chat/completions"
    )


def test_resolve_anthropic_v1_root():
    assert (
        resolve_anthropic_messages_url("https://api.anthropic.com/v1")
        == "https://api.anthropic.com/v1/messages"
    )


def test_openai_provider_custom_url():
    provider = OpenAIProvider(
        ProviderConfig(model="gpt-4o", base_url="http://localhost:8080/v1")
    )
    assert provider.chat_completions_url() == "http://localhost:8080/v1/chat/completions"


@pytest.mark.asyncio
async def test_model_override_on_default_provider():
    bot = Chatbot(default_provider="mock", storage="memory")
    resolved = bot._resolve_provider("my-custom-model-id")
    assert resolved.model == "my-custom-model-id"
    assert resolved.provider.name == "mock"


@pytest.mark.asyncio
async def test_model_override_provider_prefix():
    bot = Chatbot(
        providers={"openai": {"model": "gpt-4o", "api_key": "test-key", "base_url": "http://x/v1"}},
        default_provider="mock",
        storage="memory",
    )
    resolved = bot._resolve_provider("openai:gpt-4o-mini")
    assert resolved.provider.name == "openai"
    assert resolved.model == "gpt-4o-mini"
