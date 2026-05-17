"""MCP server registry — aggregates tools from multiple MCP servers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from chatbot.core.context import ToolContext
from chatbot.mcp.client import MCPClient
from chatbot.tools.registry import RegisteredTool, ToolRegistry


@dataclass
class MCPServer:
    """Configuration for an MCP server connection."""

    name: str
    url: str | None = None
    command: list[str] | None = None
    env: dict[str, str] = field(default_factory=dict)


class MCPRegistry:
    """Manages MCP clients and exposes their tools to ToolRegistry."""

    def __init__(self, servers: list[MCPServer] | None = None) -> None:
        self._servers = servers or []
        self._clients: dict[str, MCPClient] = {}

    def add_server(self, server: MCPServer) -> None:
        self._servers.append(server)

    async def connect_all(self) -> None:
        for server in self._servers:
            client = MCPClient(server.name, url=server.url, command=server.command)
            await client.connect()
            self._clients[server.name] = client

    async def load_tools_into(self, registry: ToolRegistry) -> None:
        if not self._clients:
            await self.connect_all()

        for _server_name, client in self._clients.items():
            mcp_tools = await client.list_tools()
            for spec in mcp_tools:
                registered_name = spec["name"]
                mcp_tool_name = spec["_mcp_tool"]
                registry.extend([_make_mcp_tool(client, registered_name, mcp_tool_name, spec)])

    async def close_all(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()


def _make_mcp_tool(
    client: MCPClient,
    registered_name: str,
    mcp_tool_name: str,
    spec: dict[str, Any],
) -> RegisteredTool:
    async def mcp_impl(ctx: ToolContext, **kwargs: Any) -> Any:
        return await client.call_tool(mcp_tool_name, kwargs)

    mcp_impl.__name__ = registered_name
    return RegisteredTool(
        name=registered_name,
        description=spec.get("description", registered_name),
        parameters_schema=spec.get("input_schema", {"type": "object", "properties": {}}),
        fn=mcp_impl,
    )
