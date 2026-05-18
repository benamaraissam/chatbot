"""Example 05 — HTTP tools with @http_tool decorator."""

import asyncio

from chatbot import Chatbot, ToolRegistry
from chatbot.tools import http_tool, register_http_tools


tools = ToolRegistry()


@http_tool(
    method="GET",
    url="https://httpbin.org/get",
    timeout=10,
    retry=2,
)
async def httpbin_get(greeting: str = "hello") -> dict:
    """Call httpbin GET endpoint (demo)."""


@tools.register
async def echo(ctx, message: str) -> dict:
    """Echo a message with user context."""
    return {"echo": message, "user_id": ctx.user.id}


register_http_tools(tools, httpbin_get)

bot = Chatbot(tools=tools, default_provider="mock", storage="memory")


async def main() -> None:
    response = await bot.send(
        "Use the echo tool with message 'test'",
        user_context={"user_id": "u1"},
    )
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
