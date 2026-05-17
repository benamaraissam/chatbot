"""Example 06 — Auto-generate tools from OpenAPI spec."""

import asyncio

from chatbot import Chatbot, ToolRegistry
from chatbot.tools import BearerAuth, from_openapi

tools = ToolRegistry()

# Petstore demo spec (public)
petstore_tools = from_openapi(
    spec_url="https://petstore3.swagger.io/api/v3/openapi.json",
    base_url="https://petstore3.swagger.io/api/v3",
    include=["findPetsByStatus"],
    timeout=15,
)
tools.extend(petstore_tools)

bot = Chatbot(tools=tools, default_provider="mock", storage="memory")


async def main() -> None:
    print(f"Loaded {len(tools)} tools from OpenAPI")
    for t in tools.list_tools():
        print(f"  - {t.name}: {t.description[:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
