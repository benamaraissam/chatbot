"""Tests for chatbot.tools.auth — BearerAuth, OAuth2Auth, ApiKeyHeaderAuth."""
from __future__ import annotations

import httpx
import pytest

from chatbot.core.context import Secrets, ToolContext, UserContext
from chatbot.tools.auth import ApiKeyHeaderAuth, BearerAuth, OAuth2Auth


def _ctx(**overrides) -> ToolContext:
    user = overrides.pop("user", None) or UserContext(id="u_1")
    return ToolContext(user=user, **overrides)


def _req() -> httpx.Request:
    return httpx.Request("GET", "https://api.example.com/items")


# ─────────────────────────────────────────────────────────────────────────────
# BearerAuth
# ─────────────────────────────────────────────────────────────────────────────

async def test_bearer_auth_with_inline_token() -> None:
    auth = BearerAuth(token="abc123")
    req = _req()
    await auth.apply(_ctx(), req)
    assert req.headers["Authorization"] == "Bearer abc123"


async def test_bearer_auth_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_TOKEN", "env-token")
    auth = BearerAuth(token_env="MY_TOKEN")
    req = _req()
    await auth.apply(_ctx(), req)
    assert req.headers["Authorization"] == "Bearer env-token"


async def test_bearer_auth_from_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MY_TOKEN", raising=False)
    auth = BearerAuth(token_env="MY_TOKEN")
    req = _req()
    # Secrets.get() looks up the attribute name exactly as passed; the
    # auth layer uses the same uppercase token_env string, so the attribute
    # must be created with the matching uppercase name.
    ctx = _ctx(secrets=Secrets(MY_TOKEN="secret-token"))
    await auth.apply(ctx, req)
    assert req.headers["Authorization"] == "Bearer secret-token"


async def test_bearer_auth_raises_when_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_TOKEN", raising=False)
    auth = BearerAuth(token_env="MISSING_TOKEN")
    with pytest.raises(ValueError, match="MISSING_TOKEN"):
        await auth.apply(_ctx(), _req())


# ─────────────────────────────────────────────────────────────────────────────
# OAuth2Auth
# ─────────────────────────────────────────────────────────────────────────────

async def test_oauth2_auth_uses_user_token() -> None:
    user = UserContext(id="u_1", oauth_tokens={"slack": "xoxb-1"})
    auth = OAuth2Auth(provider="slack")
    req = _req()
    await auth.apply(_ctx(user=user), req)
    assert req.headers["Authorization"] == "Bearer xoxb-1"


async def test_oauth2_auth_raises_when_user_lacks_token() -> None:
    auth = OAuth2Auth(provider="github")
    with pytest.raises(ValueError, match="github"):
        await auth.apply(_ctx(), _req())


# ─────────────────────────────────────────────────────────────────────────────
# ApiKeyHeaderAuth
# ─────────────────────────────────────────────────────────────────────────────

async def test_api_key_header_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHA_KEY", "live-key")
    auth = ApiKeyHeaderAuth(header="X-API-Key", key_env="ALPHA_KEY")
    req = _req()
    await auth.apply(_ctx(), req)
    assert req.headers["X-API-Key"] == "live-key"


async def test_api_key_header_from_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHA_KEY", raising=False)
    auth = ApiKeyHeaderAuth(header="X-API-Key", key_env="ALPHA_KEY")
    req = _req()
    # Match the case used by key_env so Secrets.get() finds the attribute.
    ctx = _ctx(secrets=Secrets(ALPHA_KEY="secret-key"))
    await auth.apply(ctx, req)
    assert req.headers["X-API-Key"] == "secret-key"


async def test_api_key_header_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_KEY", raising=False)
    auth = ApiKeyHeaderAuth(header="X-API-Key", key_env="MISSING_KEY")
    with pytest.raises(ValueError, match="MISSING_KEY"):
        await auth.apply(_ctx(), _req())
