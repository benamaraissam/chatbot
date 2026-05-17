"""User and tool execution context."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field


class Secrets(BaseModel):
    """Global secrets resolved from environment or host app."""

    model_config = {"extra": "allow"}

    def get(self, key: str, default: str | None = None) -> str | None:
        extra = getattr(self, key, None)
        if extra is not None:
            return str(extra)
        return os.environ.get(key.upper(), default)


class UserContext(BaseModel):
    """Per-request user identity and OAuth tokens."""

    id: str
    email: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    oauth_tokens: dict[str, str] = Field(default_factory=dict, exclude=True)

    async def oauth_token(self, provider: str) -> str:
        """Resolve OAuth token for a provider (host must populate via provider callable)."""
        token = self.oauth_tokens.get(provider)
        if not token:
            raise ValueError(f"No OAuth token for provider: {provider}")
        return token


class ToolContext:
    """Context passed to every tool invocation."""

    def __init__(
        self,
        *,
        user: UserContext,
        conversation_id: str | None = None,
        secrets: Secrets | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.user = user
        self.conversation_id = conversation_id
        self.secrets = secrets or Secrets()
        self.metadata = metadata or {}


UserContextProvider = Callable[..., UserContext | Awaitable[UserContext]]
