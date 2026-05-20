"""Tests for chatbot.mcp.client — MCPClient constructor and config validation."""
from __future__ import annotations

import pytest

from chatbot.mcp.client import MCPClient


# ─────────────────────────────────────────────────────────────────────────────
# Construction
# ─────────────────────────────────────────────────────────────────────────────

def test_constructor_stores_name_and_url() -> None:
    client = MCPClient("notion", url="https://example.com/mcp")
    assert client.name == "notion"
    assert client.url == "https://example.com/mcp"
    assert client.command is None


def test_constructor_stores_command() -> None:
    client = MCPClient("local-tool", command=["mcp-server", "--port", "9000"])
    assert client.name == "local-tool"
    assert client.command == ["mcp-server", "--port", "9000"]
    assert client.url is None


def test_session_is_initially_none() -> None:
    client = MCPClient("x", url="https://example.com")
    # Internal session is lazy-initialised on connect().
    assert client._session is None


# ─────────────────────────────────────────────────────────────────────────────
# connect() — error paths exercised without a real MCP server
# ─────────────────────────────────────────────────────────────────────────────

async def test_connect_without_url_or_command_raises() -> None:
    client = MCPClient("orphan")
    with pytest.raises(ValueError, match="url or command"):
        await client.connect()


async def test_close_is_a_noop_when_never_connected() -> None:
    client = MCPClient("x", url="https://example.com")
    # close() should not raise when no session was established.
    await client.close()
    assert client._session is None
