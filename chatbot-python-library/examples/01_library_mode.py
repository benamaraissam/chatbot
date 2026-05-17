"""Example 01 — Library mode (async iterator, no HTTP server)."""

import asyncio

from chatbot import Chatbot, TextDelta


async def main() -> None:
    bot = Chatbot(provider="mock", storage="memory")

    print("=== send() ===")
    response = await bot.send("Hello, what can you do?", user_context={"user_id": "demo"})
    print(response.text)

    print("\n=== stream() ===")
    async for event in bot.stream("Tell me a joke"):
        if isinstance(event, TextDelta):
            print(event.delta, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
