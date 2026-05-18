"""FastAPI variant of the demo app.

Run from the repo root::

    python examples/02_web_apps/fastapi_app.py

Or with uvicorn directly (for --reload, working-dir matters)::

    cd examples/02_web_apps && uvicorn fastapi_app:app --reload --port 8000

The bot, tools, and provider config are shared with the Flask and Django
variants (see ``bot.py`` / ``tools.py`` in this directory).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make sibling modules importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI

from chatbot.env import load_dotenv_file
from chatbot.integrations.fastapi import create_router
from chatbot.providers.mock_scenarios import DEMO_HINTS

from bot import build_bot, configured_providers  # noqa: E402  — sibling import
from tools import build_tools  # noqa: E402

# Load chatbot-python-library/.env if present.
load_dotenv_file(Path(__file__).resolve().parents[2] / ".env")


# ---------------------------------------------------------------------------
# Framework wiring
# ---------------------------------------------------------------------------

app = FastAPI(title="Chatbot demo — FastAPI")

tools = build_tools()
bot = build_bot(tools)


def get_user_context() -> dict:
    """Stub auth — replace with FastAPI Depends(...) on your current-user dep."""
    return {"user_id": "user_42", "email": "user@example.com"}


app.include_router(
    create_router(bot, user_context=get_user_context),
    prefix="/api/chat",
    tags=["chatbot"],
)


# ---------------------------------------------------------------------------
# Health / discovery
# ---------------------------------------------------------------------------


@app.get("/")
async def root() -> dict:
    return {
        "framework": "fastapi",
        "default_provider": bot._default_provider,
        "providers": list(bot.providers.names),
        "configured_providers": configured_providers(),
        "tools": [t.name for t in tools.list_tools()],
        "openai_key_set": bool(os.environ.get("OPENAI_API_KEY")),
        "azure_endpoint_set": bool(os.environ.get("AZURE_OPENAI_ENDPOINT")),
        "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "try_in_chat": [h["message"] for h in DEMO_HINTS],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
