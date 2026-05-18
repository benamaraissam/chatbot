"""Azure OpenAI provider — URL building, auth headers, registry wiring."""

from __future__ import annotations

import pytest

from chatbot import Chatbot
from chatbot.providers import AzureOpenAIProvider, OpenAIProvider
from chatbot.providers.base import ProviderConfig, build_default_registry
from chatbot.providers.openai_messages import should_include_stream_usage
from chatbot.providers.urls import (
    DEFAULT_AZURE_OPENAI_API_VERSION,
    resolve_azure_openai_chat_completions_url,
)


# ---------------------------------------------------------------------------
# URL builder
# ---------------------------------------------------------------------------


def test_azure_url_from_resource_root():
    url = resolve_azure_openai_chat_completions_url(
        "https://my-resource.openai.azure.com",
        "gpt-4o-prod",
        api_version="2024-10-21",
    )
    assert url == (
        "https://my-resource.openai.azure.com/openai/deployments/gpt-4o-prod"
        "/chat/completions?api-version=2024-10-21"
    )


def test_azure_url_trims_trailing_slash():
    url = resolve_azure_openai_chat_completions_url(
        "https://my-resource.openai.azure.com/",
        "my-dep",
        api_version="2024-08-01-preview",
    )
    assert url.startswith(
        "https://my-resource.openai.azure.com/openai/deployments/my-dep/chat/completions"
    )
    assert "api-version=2024-08-01-preview" in url


def test_azure_url_endpoint_already_has_openai_suffix():
    url = resolve_azure_openai_chat_completions_url(
        "https://my-resource.openai.azure.com/openai",
        "dep",
        api_version="2024-10-21",
    )
    assert (
        url
        == "https://my-resource.openai.azure.com/openai/deployments/dep/chat/completions?api-version=2024-10-21"
    )


def test_azure_url_with_full_deployment_path():
    full = "https://my-resource.openai.azure.com/openai/deployments/dep/chat/completions"
    url = resolve_azure_openai_chat_completions_url(full, "dep", api_version="2024-10-21")
    assert url.endswith("/chat/completions?api-version=2024-10-21")
    assert "/openai/deployments/dep/chat/completions" in url


def test_azure_url_api_version_from_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    url = resolve_azure_openai_chat_completions_url(
        "https://my-resource.openai.azure.com", "dep"
    )
    assert url.endswith("api-version=2024-12-01-preview")


def test_azure_url_endpoint_from_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://envres.openai.azure.com")
    url = resolve_azure_openai_chat_completions_url(None, "dep", api_version="2024-10-21")
    assert url.startswith("https://envres.openai.azure.com/openai/deployments/dep/")


def test_azure_url_default_api_version(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    url = resolve_azure_openai_chat_completions_url(
        "https://my-resource.openai.azure.com", "dep"
    )
    assert url.endswith(f"api-version={DEFAULT_AZURE_OPENAI_API_VERSION}")


def test_azure_url_requires_deployment():
    with pytest.raises(ValueError, match="deployment"):
        resolve_azure_openai_chat_completions_url(
            "https://my-resource.openai.azure.com", "", api_version="2024-10-21"
        )


def test_azure_url_requires_endpoint(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    with pytest.raises(ValueError, match="endpoint"):
        resolve_azure_openai_chat_completions_url(None, "dep")


def test_azure_url_preserves_existing_query():
    url = resolve_azure_openai_chat_completions_url(
        "https://my-resource.openai.azure.com/openai/deployments/dep/chat/completions?foo=bar",
        "dep",
        api_version="2024-10-21",
    )
    assert "foo=bar" in url
    assert "api-version=2024-10-21" in url


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------


def test_azure_provider_request_url_uses_effective_model():
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="prod-dep",
            base_url="https://my-resource.openai.azure.com",
            api_key="dummy",
            extra={"api_version": "2024-10-21"},
        )
    )
    # Default (configured) model
    assert provider._request_url("prod-dep").endswith(
        "/openai/deployments/prod-dep/chat/completions?api-version=2024-10-21"
    )
    # Per-request override → URL must reflect the override
    assert provider._request_url("preview-dep").endswith(
        "/openai/deployments/preview-dep/chat/completions?api-version=2024-10-21"
    )


def test_azure_provider_auth_header_api_key():
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="dep",
            base_url="https://my-resource.openai.azure.com",
            api_key="secret-key",
            extra={"api_version": "2024-10-21"},
        )
    )
    headers = provider._auth_headers()
    assert headers["api-key"] == "secret-key"
    assert "Authorization" not in headers
    assert headers["Content-Type"] == "application/json"


def test_azure_provider_auth_header_aad_via_extra():
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="dep",
            base_url="https://my-resource.openai.azure.com",
            extra={
                "api_version": "2024-10-21",
                "use_aad": True,
                "azure_ad_token": "aad-token-abc",
            },
        )
    )
    headers = provider._auth_headers()
    assert headers["Authorization"] == "Bearer aad-token-abc"
    assert "api-key" not in headers


def test_azure_provider_auth_header_aad_via_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_AD_TOKEN", "env-token-xyz")
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="dep",
            base_url="https://my-resource.openai.azure.com",
            extra={"api_version": "2024-10-21", "use_aad": True},
        )
    )
    headers = provider._auth_headers()
    assert headers["Authorization"] == "Bearer env-token-xyz"


def test_azure_provider_aad_implicit_from_token_env_setting(monkeypatch):
    """Configuring azure_ad_token_env should auto-enable AAD without use_aad=True."""
    monkeypatch.setenv("MY_AAD_TOKEN", "implicit-token")
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="dep",
            base_url="https://my-resource.openai.azure.com",
            extra={"api_version": "2024-10-21", "azure_ad_token_env": "MY_AAD_TOKEN"},
        )
    )
    headers = provider._auth_headers()
    assert headers["Authorization"] == "Bearer implicit-token"


def test_azure_provider_aad_missing_token_raises():
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="dep",
            base_url="https://my-resource.openai.azure.com",
            extra={"api_version": "2024-10-21", "use_aad": True},
        )
    )
    with pytest.raises(ValueError, match="use_aad"):
        provider._auth_headers()


def test_azure_provider_missing_api_key_raises():
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="dep",
            base_url="https://my-resource.openai.azure.com",
            extra={"api_version": "2024-10-21"},
        )
    )
    with pytest.raises(ValueError, match="Azure OpenAI provider needs an API key"):
        provider._auth_headers()


def test_azure_provider_api_key_from_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "env-azure-key")
    provider = AzureOpenAIProvider(
        ProviderConfig(
            model="dep",
            base_url="https://my-resource.openai.azure.com",
            extra={"api_version": "2024-10-21"},
        )
    )
    headers = provider._auth_headers()
    assert headers["api-key"] == "env-azure-key"


def test_azure_provider_pydantic_ai_model():
    provider = AzureOpenAIProvider(
        ProviderConfig(model="my-dep", base_url="https://x.openai.azure.com", api_key="k")
    )
    assert provider.pydantic_ai_model() == "azure:my-dep"


# ---------------------------------------------------------------------------
# Registry / integration
# ---------------------------------------------------------------------------


def test_registry_resolves_azure_alias():
    registry = build_default_registry(
        {
            "azure": {
                "model": "my-deployment",
                "api_key": "k",
                "base_url": "https://my-resource.openai.azure.com",
                "extra": {"api_version": "2024-10-21"},
            }
        }
    )
    provider = registry.get("azure")
    assert isinstance(provider, AzureOpenAIProvider)


def test_registry_resolves_azure_openai_alias():
    registry = build_default_registry(
        {
            "azure_openai": {
                "model": "my-dep",
                "api_key": "k",
                "base_url": "https://my-resource.openai.azure.com",
            }
        }
    )
    assert isinstance(registry.get("azure_openai"), AzureOpenAIProvider)


def test_openai_provider_unaffected_by_azure_changes():
    """Refactor must not break the plain OpenAI provider."""
    provider = OpenAIProvider(
        ProviderConfig(model="gpt-4o", base_url="https://api.openai.com/v1", api_key="k")
    )
    headers = provider._auth_headers()
    assert headers["Authorization"] == "Bearer k"
    assert provider._request_url("gpt-4o") == "https://api.openai.com/v1/chat/completions"


def test_stream_usage_enabled_for_azure_hosts():
    azure_url = (
        "https://my-resource.openai.azure.com/openai/deployments/dep/chat/completions"
        "?api-version=2024-10-21"
    )
    assert should_include_stream_usage(azure_url) is True


@pytest.mark.asyncio
async def test_chatbot_can_register_azure_provider():
    bot = Chatbot(
        providers={
            "azure": {
                "model": "my-deployment",
                "api_key": "k",
                "base_url": "https://my-resource.openai.azure.com",
                "extra": {"api_version": "2024-10-21"},
            }
        },
        default_provider="azure",
        storage="memory",
    )
    resolved = bot._resolve_provider(None)
    assert isinstance(resolved.provider, AzureOpenAIProvider)
    # Per-request deployment override via "provider:deployment"
    resolved2 = bot._resolve_provider("azure:other-deployment")
    assert resolved2.provider.name == "azure_openai"
    assert resolved2.model == "other-deployment"
