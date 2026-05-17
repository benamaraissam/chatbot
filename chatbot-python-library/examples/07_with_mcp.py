"""Example 07 — MCP server integration."""

import asyncio

from chatbot import Chatbot
from chatbot.mcp import MCPServer

# Configure MCP servers (stdio or SSE)
mcp_servers = [
    # MCPServer(name="github", command=["uvx", "mcp-server-github"]),
    # MCPServer(name="notion", url="https://mcp.notion.com/sse"),
]

bot = Chatbot(
    mcp_servers=mcp_servers,
    default_provider="mock",
    storage="memory",
)


async def main() -> None:
    if not mcp_servers:
        print("Configure MCPServer entries in mcp_servers to connect.")
        return
    response = await bot.send("List available MCP tools")
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
