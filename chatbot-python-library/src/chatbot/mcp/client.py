"""MCP client wrapper using the official MCP Python SDK."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPClient:
    """Connect to an MCP server and list/call tools."""

    def __init__(
        self,
        name: str,
        *,
        url: str | None = None,
        command: list[str] | None = None,
    ) -> None:
        self.name = name
        self.url = url
        self.command = command
        self._session: Any = None

    async def connect(self) -> None:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise ImportError("MCP SDK required: pip install mcp") from exc

        if self.command:
            params = StdioServerParameters(command=self.command[0], args=self.command[1:])
            self._transport = stdio_client(params)
            read, write = await self._transport.__aenter__()
            self._session = ClientSession(read, write)
            await self._session.__aenter__()
            await self._session.initialize()
        elif self.url:
            # SSE transport — simplified; full impl depends on mcp version
            logger.warning(
                "MCP SSE URL transport for %s: connect at runtime via host app",
                self.name,
            )
        else:
            raise ValueError(f"MCP server {self.name} needs url or command")

    async def list_tools(self) -> list[dict[str, Any]]:
        if not self._session:
            await self.connect()
        result = await self._session.list_tools()
        return [
            {
                "name": f"mcp_{self.name}_{t.name}",
                "description": t.description or t.name,
                "input_schema": t.inputSchema,
                "_mcp_tool": t.name,
            }
            for t in result.tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if not self._session:
            await self.connect()
        result = await self._session.call_tool(tool_name, arguments)
        if result.content:
            first = result.content[0]
            return first.model_dump() if hasattr(first, "model_dump") else result.content
        return None

    async def close(self) -> None:
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None
