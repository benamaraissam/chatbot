"""FastAPI demo app.

Run from the repo root:

    python examples/02_web_apps/fastapi_app.py

Or with live reload:

    cd examples/02_web_apps && uvicorn fastapi_app:app --reload --port 8000

CORS origins default to the common local dev ports (3000, 4200, 5173).
Override with ``CORS_ORIGINS=https://app.example.com`` or set
``CORS_ALLOW_ALL=true`` during development.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running as a script from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbot.env import load_dotenv_file
from chatbot.integrations.fastapi import create_router

from bot import build_bot, configured_providers
from tools import build_tools

# Load .env from the library root if present.
load_dotenv_file(Path(__file__).resolve().parents[2] / ".env")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Chatbot demo — FastAPI")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

_allow_all = os.environ.get("CORS_ALLOW_ALL", "").lower() in ("1", "true", "yes")
_raw_origins = os.environ.get("CORS_ORIGINS", "")

if _allow_all:
    _origins = ["*"]
elif _raw_origins:
    _origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
else:
    _origins = [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------

tools = build_tools()
bot = build_bot(tools)


def get_user_context() -> dict:
    """Stub auth — replace with a real FastAPI dependency."""
    return {"user_id": "user_42", "email": "user@example.com"}


app.include_router(
    create_router(bot, user_context=get_user_context),
    prefix="/api/chat",
    tags=["chatbot"],
)

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/")
async def health() -> dict:
    return {
        "status": "ok",
        "default_provider": bot._default_provider,
        "configured_providers": configured_providers(),
        "tools": [t.name for t in tools.list_tools()],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
