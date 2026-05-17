"""Example 09 — OpenAI-compatible API with custom base URL and model."""

import asyncio
import os

from chatbot import Chatbot

# Ollama (OpenAI-compatible) — no API key required locally
OLLAMA_BASE = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

bot = Chatbot(
    providers={
        "openai": {
            "model": OLLAMA_MODEL,
            "base_url": OLLAMA_BASE,
            "api_key": os.environ.get("OPENAI_API_KEY", "ollama"),
        },
    },
    default_provider="openai",
    storage="memory",
)


async def main() -> None:
    # Default model from config
    print("Configured URL:", bot.providers.get("openai").chat_completions_url())

    # Per-request model override
    response = await bot.send("Say hi in one sentence.", model="llama3.2")
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
