"""Example 02 — FastAPI + mock provider with rich UI demo scenarios."""

import os
from pathlib import Path

from fastapi import FastAPI

import httpx

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


# BNP Paribas AM fund-search API returns a very large payload (hundreds of funds
# with rich metadata). Sending the raw JSON back to the LLM blows past model
# context limits (Moonshot 256k was overflowed at ~685k tokens). We project
# each fund down to a small set of useful fields and paginate so the tool
# result stays within budget. Use offset/limit to page through more results.

_FUND_FIELDS = (
    "fund_name",
    "fundname",
    "name",
    "isin",
    "currency",
    "ccy",
    "asset_class",
    "category",
    "share_class",
    "share_class_name",
    "domicile",
    "ytd",
    "nav",
    "perf_ytd",
    "perf_1y",
    "perf_3y",
)


def _project_fund(item: dict) -> dict:
    """Keep only short scalar fields useful for the LLM."""
    out: dict = {}
    for key in _FUND_FIELDS:
        if key in item and isinstance(item[key], (str, int, float, bool)) and item[key] is not None:
            value = item[key]
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "…"
            out[key] = value
    # Always keep a stable id-like field if present.
    for id_key in ("id", "fund_id", "isin", "ticker"):
        if id_key in item and id_key not in out:
            out[id_key] = item[id_key]
    return out


def _extract_fund_list(payload) -> list[dict]:
    """Find the largest list of fund-like dicts inside the response."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        best: list[dict] = []
        for value in payload.values():
            if isinstance(value, list):
                candidates = [x for x in value if isinstance(x, dict)]
                if len(candidates) > len(best):
                    best = candidates
        return best
    return []


@tools.register
async def bnpp_fund_search(
    ctx,
    profile: str = "PV_LU-FSE",
    language: str = "ENG",
    limit: int = 25,
    offset: int = 0,
) -> dict:
    """Search BNP Paribas AM funds and return a paginated, slim projection.

    Args:
        profile: Country/platform profile (e.g. ``PV_LU-FSE``).
        language: Two-or-three-letter language code (e.g. ``ENG``).
        limit: Max funds to return per call (1–50). Use offset to page.
        offset: Index of the first fund to return (0-based).
    """
    limit = max(1, min(int(limit), 50))
    offset = max(0, int(offset))
    url = (
        f"https://api.bnpparibas-am.com/push/fundsearchv2/{profile}/{language}"
        "?without_has_docs=True&action_column_tool=fundpanorama"
    )
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        payload = resp.json()

    funds = _extract_fund_list(payload)
    total = len(funds)
    page = [_project_fund(f) for f in funds[offset : offset + limit]]
    return {
        "profile": profile,
        "language": language,
        "total": total,
        "offset": offset,
        "limit": limit,
        "returned": len(page),
        "has_more": offset + len(page) < total,
        "items": page,
    }


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
