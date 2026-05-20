"""Tests for UserContext, Secrets, and ToolContext."""
from __future__ import annotations

import pytest

from chatbot.core.context import Secrets, ToolContext, UserContext


# ─────────────────────────────────────────────────────────────────────────────
# UserContext
# ─────────────────────────────────────────────────────────────────────────────

def test_user_context_minimal_fields() -> None:
    user = UserContext(id="u1")
    assert user.id == "u1"
    assert user.email is None
    assert user.metadata == {}
    assert user.oauth_tokens == {}


def test_user_context_full_fields() -> None:
    user = UserContext(
        id="u1",
        email="alice@example.com",
        metadata={"role": "trader"},
        oauth_tokens={"slack": "xoxb-123"},
    )
    assert user.email == "alice@example.com"
    assert user.metadata["role"] == "trader"


def test_user_context_oauth_tokens_excluded_from_serialization() -> None:
    user = UserContext(
        id="u1",
        oauth_tokens={"slack": "secret-token"},
    )
    dumped = user.model_dump()
    # OAuth tokens must never leak through model_dump (PII / secret).
    assert "oauth_tokens" not in dumped
    assert "secret-token" not in str(dumped)


async def test_oauth_token_returns_configured_token() -> None:
    user = UserContext(id="u1", oauth_tokens={"github": "ghp_xxx"})
    assert await user.oauth_token("github") == "ghp_xxx"


async def test_oauth_token_missing_raises_with_provider_name() -> None:
    user = UserContext(id="u1")
    with pytest.raises(ValueError, match="github"):
        await user.oauth_token("github")


# ─────────────────────────────────────────────────────────────────────────────
# Secrets
# ─────────────────────────────────────────────────────────────────────────────

def test_secrets_explicit_value_wins_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "from-env")
    secrets = Secrets(api_key="from-explicit")
    assert secrets.get("api_key") == "from-explicit"


def test_secrets_falls_back_to_env_uppercased(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_KEY", "from-env")
    secrets = Secrets()
    assert secrets.get("my_key") == "from-env"


def test_secrets_returns_default_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOES_NOT_EXIST", raising=False)
    secrets = Secrets()
    assert secrets.get("does_not_exist", default="fallback") == "fallback"


def test_secrets_returns_none_when_missing_and_no_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MISSING_X", raising=False)
    secrets = Secrets()
    assert secrets.get("missing_x") is None


# ─────────────────────────────────────────────────────────────────────────────
# ToolContext
# ─────────────────────────────────────────────────────────────────────────────

def test_tool_context_defaults() -> None:
    user = UserContext(id="u1")
    ctx = ToolContext(user=user)
    assert ctx.user is user
    assert ctx.conversation_id is None
    assert isinstance(ctx.secrets, Secrets)
    assert ctx.metadata == {}


def test_tool_context_full() -> None:
    user = UserContext(id="u1")
    secrets = Secrets(custom="x")
    ctx = ToolContext(
        user=user,
        conversation_id="conv_42",
        secrets=secrets,
        metadata={"trace_id": "t1"},
    )
    assert ctx.conversation_id == "conv_42"
    assert ctx.secrets is secrets
    assert ctx.metadata["trace_id"] == "t1"
