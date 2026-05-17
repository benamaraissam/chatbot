"""Example 02 — FastAPI + mock provider with rich UI demo scenarios."""

import os
from pathlib import Path

from fastapi import FastAPI

from chatbot import Chatbot, ToolRegistry
from chatbot.env import load_dotenv_file
from chatbot.integrations.fastapi import create_router
from chatbot.providers.mock_scenarios import DEMO_HINTS

# Load chatbot-python-library/.env (see .env.example)
load_dotenv_file(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="My App with Chatbot")

tools = ToolRegistry()


@tools.register
async def get_weather(ctx, city: str = "Paris") -> dict:
    """Return mock weather for a city."""
    return {
        "city": city,
        "temperature_c": 18,
        "condition": "sunny",
        "humidity_pct": 42,
    }


@tools.register
async def search_docs(ctx, query: str, limit: int = 5) -> dict:
    """Search knowledge base (mock)."""
    return {
        "query": query,
        "results": [
            {"title": f"Article {i + 1}", "snippet": f"Match for '{query}'…"}
            for i in range(min(limit, 3))
        ],
    }


@tools.register(requires_approval=True)
async def send_email(ctx, to: str, subject: str, body: str) -> dict:
    """Send an email — requires user approval in the chat UI."""
    return {"status": "sent", "to": to, "subject": subject}


@tools.register
async def simulate_failure(ctx, reason: str = "unknown") -> dict:
    """Always fails — demos error state in tool cards."""
    raise RuntimeError(f"Simulated failure: {reason}")


bot = Chatbot(
    providers={
        "mock": {"model": "mock"},
        "openai": {
            "model": os.environ.get("CHATBOT_OPENAI_MODEL", "gpt-4o"),
            "api_key_env": "OPENAI_API_KEY",
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        },
    },
    default_provider=os.environ.get("CHATBOT_DEFAULT_PROVIDER", "mock"),
    storage="memory",
    tools=tools,
)


def get_user_context():
    return {"user_id": "user_42", "email": "user@example.com"}


app.include_router(
    create_router(bot, user_context=get_user_context),
    prefix="/api/chat",
    tags=["chatbot"],
)


@app.get("/")
async def root():
    return {
        "message": "Chatbot demo — POST /api/chat/chat for SSE",
        "default_provider": bot._default_provider,
        "providers": list(bot.providers.names),
        "openai_key_set": bool(os.environ.get("OPENAI_API_KEY")),
        "try_in_chat": [h["message"] for h in DEMO_HINTS],
        "hints": DEMO_HINTS,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
