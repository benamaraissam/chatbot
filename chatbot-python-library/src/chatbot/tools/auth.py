"""Authentication helpers for HTTP and OpenAPI tools."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from chatbot.core.context import ToolContext


class AuthScheme(ABC):
    @abstractmethod
    async def apply(self, ctx: ToolContext, request: httpx.Request) -> None:
        """Mutate request with auth headers."""


class BearerAuth(AuthScheme):
    def __init__(self, token: str | None = None, token_env: str | None = None) -> None:
        self.token = token
        self.token_env = token_env

    def resolve_token(self, ctx: ToolContext) -> str:
        if self.token:
            return self.token
        if self.token_env:
            value = os.environ.get(self.token_env) or ctx.secrets.get(self.token_env)
            if value:
                return value
        raise ValueError(f"Bearer token not found (env: {self.token_env})")

    async def apply(self, ctx: ToolContext, request: httpx.Request) -> None:
        request.headers["Authorization"] = f"Bearer {self.resolve_token(ctx)}"


class OAuth2Auth(AuthScheme):
    """Per-user OAuth via ToolContext.user.oauth_token()."""

    def __init__(self, provider: str) -> None:
        self.provider = provider

    async def apply(self, ctx: ToolContext, request: httpx.Request) -> None:
        token = await ctx.user.oauth_token(self.provider)
        request.headers["Authorization"] = f"Bearer {token}"


class ApiKeyHeaderAuth(AuthScheme):
    def __init__(self, header: str, key_env: str) -> None:
        self.header = header
        self.key_env = key_env

    async def apply(self, ctx: ToolContext, request: httpx.Request) -> None:
        key = os.environ.get(self.key_env) or ctx.secrets.get(self.key_env)
        if not key:
            raise ValueError(f"API key not found: {self.key_env}")
        request.headers[self.header] = key
