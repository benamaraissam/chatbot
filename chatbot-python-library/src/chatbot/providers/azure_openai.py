"""Azure OpenAI provider.

Built as a thin subclass of :class:`OpenAIProvider` — the wire format is identical
to OpenAI Chat Completions, but the URL, model→deployment mapping, and auth
header differ.

Configuration (via ``ProviderConfig``):

- ``model``       — Azure **deployment name** (e.g. ``gpt-4o-prod``). Per-request
                    model overrides are also treated as deployment names.
- ``base_url`` / ``base_url_env`` — Azure endpoint, e.g.
                    ``https://my-resource.openai.azure.com``. Falls back to
                    the ``AZURE_OPENAI_ENDPOINT`` env var.
- ``api_key`` / ``api_key_env`` — Azure API key. Falls back to
                    the ``AZURE_OPENAI_API_KEY`` env var.
- ``extra.api_version`` — Azure API version (e.g. ``2024-10-21``). Falls back to
                    ``AZURE_OPENAI_API_VERSION`` env, then a sensible default.
- ``extra.use_aad`` — Set to ``True`` to authenticate with an Entra ID
                    (Azure AD) bearer token instead of an API key.
- ``extra.azure_ad_token`` / ``extra.azure_ad_token_env`` — Bearer token (or env
                    var name) used when ``use_aad`` is on. Falls back to
                    ``AZURE_OPENAI_AD_TOKEN``.
"""

from __future__ import annotations

import os
from typing import Any

from chatbot.providers.openai import OpenAIProvider
from chatbot.providers.urls import resolve_azure_openai_chat_completions_url

AZURE_ENDPOINT_ENV = "AZURE_OPENAI_ENDPOINT"
AZURE_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
AZURE_API_VERSION_ENV = "AZURE_OPENAI_API_VERSION"
AZURE_AD_TOKEN_ENV = "AZURE_OPENAI_AD_TOKEN"


class AzureOpenAIProvider(OpenAIProvider):
    """OpenAI-compatible provider speaking the Azure OpenAI dialect."""

    name = "azure_openai"

    def pydantic_ai_model(self) -> str:
        # pydantic-ai uses ``azure:<deployment>`` for its Azure model identifier.
        return f"azure:{self.config.model}"

    # ----- URL ---------------------------------------------------------------

    def _request_url(self, effective_model: str) -> str:
        endpoint = self.config.resolve_base_url(default_env=AZURE_ENDPOINT_ENV)
        api_version = self._resolve_api_version()
        return resolve_azure_openai_chat_completions_url(
            endpoint,
            effective_model,
            api_version=api_version,
        )

    def chat_completions_url(self) -> str:  # type: ignore[override]
        """Compatibility shim — builds URL using the configured default deployment."""
        return self._request_url(self.config.model)

    # ----- Auth --------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:  # type: ignore[override]
        if self._use_aad():
            token = self._resolve_aad_token_or_raise()
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        api_key = self._resolve_api_key_or_raise()
        return {
            "api-key": api_key,
            "Content-Type": "application/json",
        }

    def _resolve_api_key_or_raise(self) -> str:  # type: ignore[override]
        try:
            api_key = self.config.resolve_api_key()
        except ValueError:
            raise
        api_key = api_key or os.environ.get(AZURE_API_KEY_ENV)
        if not api_key:
            raise ValueError(
                "Azure OpenAI provider needs an API key: set providers.<name>.api_key, "
                "providers.<name>.api_key_env (e.g. AZURE_OPENAI_API_KEY) with that variable "
                "exported, or export AZURE_OPENAI_API_KEY in the shell. For Entra ID auth, "
                "set providers.<name>.extra.use_aad=true and provide an Azure AD token."
            )
        return api_key

    # ----- Azure-specific helpers -------------------------------------------

    def _resolve_api_version(self) -> str | None:
        extra: dict[str, Any] = self.config.extra or {}
        return extra.get("api_version")

    def _use_aad(self) -> bool:
        extra: dict[str, Any] = self.config.extra or {}
        flag = extra.get("use_aad")
        if isinstance(flag, bool):
            return flag
        if isinstance(flag, str):
            return flag.strip().lower() in ("1", "true", "yes", "on")
        # Implicit AAD: an explicit token (or token env) is configured.
        return bool(extra.get("azure_ad_token") or extra.get("azure_ad_token_env"))

    def _resolve_aad_token_or_raise(self) -> str:
        extra: dict[str, Any] = self.config.extra or {}
        token = extra.get("azure_ad_token")
        if not token:
            env_name = extra.get("azure_ad_token_env") or AZURE_AD_TOKEN_ENV
            token = os.environ.get(env_name)
        if not token:
            raise ValueError(
                "Azure OpenAI provider configured with use_aad=true but no token found. "
                "Set providers.<name>.extra.azure_ad_token, "
                "providers.<name>.extra.azure_ad_token_env, or export "
                "AZURE_OPENAI_AD_TOKEN before starting the server."
            )
        return str(token)
