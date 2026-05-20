"""Tests for chatbot.mcp.registry — MCPRegistry config and tool wiring."""
from __future__ import annotations

import pytest

from chatbot.mcp.registry import MCPRegistry, MCPServer


def test_mcp_server_dataclass_defaults() -> None:
    s = MCPServer(name="notion", url="https://example.com/mcp")
    assert s.name == "notion"
    assert s.url == "https://example.com/mcp"
    assert s.command is None
    assert s.env == {}


def test_mcp_server_with_command_and_env() -> None:
    s = MCPServer(
        name="local-tool",
        command=["mcp-server", "--port", "9000"],
        env={"DEBUG": "1"},
    )
    assert s.command == ["mcp-server", "--port", "9000"]
    assert s.env == {"DEBUG": "1"}
    assert s.url is None


def test_registry_starts_empty_by_default() -> None:
    reg = MCPRegistry()
    assert reg._servers == []
    assert reg._clients == {}


def test_registry_accepts_initial_servers() -> None:
    servers = [MCPServer(name="a", url="https://x"), MCPServer(name="b", url="https://y")]
    reg = MCPRegistry(servers)
    assert len(reg._servers) == 2


def test_add_server_appends_to_internal_list() -> None:
    reg = MCPRegistry()
    reg.add_server(MCPServer(name="a", url="https://x"))
    reg.add_server(MCPServer(name="b", url="https://y"))
    assert [s.name for s in reg._servers] == ["a", "b"]


async def test_close_all_is_safe_when_never_connected() -> None:
    reg = MCPRegistry([MCPServer(name="a", url="https://x")])
    # No clients were ever created, so close_all should be a no-op.
    await reg.close_all()
    assert reg._clients == {}
