"""URL normalization for OpenAI-compatible and Anthropic API endpoints."""

from __future__ import annotations

import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

DEFAULT_AZURE_OPENAI_API_VERSION = "2024-10-21"


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


def resolve_azure_openai_chat_completions_url(
    endpoint: str | None,
    deployment: str,
    *,
    api_version: str | None = None,
    endpoint_env: str = "AZURE_OPENAI_ENDPOINT",
    api_version_env: str = "AZURE_OPENAI_API_VERSION",
) -> str:
    """
    Build the Azure OpenAI chat completions URL.

    Accepts ``endpoint`` as:
    - Resource root: ``https://my-resource.openai.azure.com`` (or with trailing ``/``)
    - With ``/openai`` suffix: ``https://my-resource.openai.azure.com/openai``
    - Full deployment URL: ``https://.../openai/deployments/<dep>/chat/completions``
      (in which case the deployment in the URL takes precedence, but ``api-version``
      query param is still ensured)

    Falls back to ``AZURE_OPENAI_ENDPOINT`` env var when ``endpoint`` is omitted.
    ``api_version`` falls back to ``AZURE_OPENAI_API_VERSION`` env, then
    :data:`DEFAULT_AZURE_OPENAI_API_VERSION`.
    """
    if not deployment:
        raise ValueError(
            "Azure OpenAI requires a deployment name. Set providers.<name>.model "
            "to the deployment name configured in your Azure portal."
        )

    raw_endpoint = (endpoint or os.environ.get(endpoint_env) or "").strip()
    if not raw_endpoint:
        raise ValueError(
            "Azure OpenAI provider needs an endpoint: set providers.<name>.base_url, "
            "providers.<name>.base_url_env (e.g. AZURE_OPENAI_ENDPOINT) with that variable "
            "exported, or export AZURE_OPENAI_ENDPOINT in the shell before starting the "
            "server. Example: https://my-resource.openai.azure.com"
        )

    raw_endpoint = raw_endpoint.rstrip("/")
    parsed = urlparse(raw_endpoint)
    path = parsed.path.rstrip("/")

    if "/chat/completions" in path:
        new_path = path
    elif "/deployments/" in path:
        new_path = f"{path}/chat/completions"
    elif path.endswith("/openai"):
        new_path = f"{path}/deployments/{deployment}/chat/completions"
    else:
        new_path = f"{path}/openai/deployments/{deployment}/chat/completions"

    version = (
        api_version
        or os.environ.get(api_version_env)
        or DEFAULT_AZURE_OPENAI_API_VERSION
    ).strip()

    existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
    existing.setdefault("api-version", version)
    new_query = urlencode(existing)

    return urlunparse(parsed._replace(path=new_path, query=new_query))


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
