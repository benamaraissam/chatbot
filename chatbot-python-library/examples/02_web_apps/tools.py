"""Tools shared by the FastAPI, Flask, and Django variants.

This file showcases every tool-authoring style the library supports:

1. **Plain async function** registered via ``@tools.register`` — simple
   deterministic mocks (``get_weather``, ``search_docs``).
2. **Context-aware** tool — reads ``ctx.user.id`` and ``ctx.secrets``
   (``whoami``).
3. **Cached** tool — repeated calls within ``cache_ttl`` are served from memory
   (``list_currencies``).
4. **Rate-limited** tool — caps per-user QPS (``rate_limited_ping``).
5. **Approval-required** tool — the React UI must Approve before execution
   (``send_email``).
6. **Error-state** tool — always raises, drives the UI's error rendering
   (``simulate_failure``).
7. **HTTP-only tool** via ``@http_tool`` — declarative REST call with retry +
   path templating (``get_exchange_rate``).
8. **Paginated + HTTP-only stack** via ``@paginated @http_tool`` — the decorator
   stack does fetch, projection, slicing, and envelope (``bnpp_fund_search``).
"""

from __future__ import annotations

from chatbot import ToolRegistry, paginated
from chatbot.core.context import ToolContext
from chatbot.tools import http_tool


# ---------------------------------------------------------------------------
# 1. Plain registered tools (deterministic mocks)
# ---------------------------------------------------------------------------


async def _get_weather(ctx: ToolContext, city: str = "Paris") -> dict:
    """Return mock weather for a city."""
    return {
        "city": city,
        "temperature_c": 18,
        "condition": "sunny",
        "humidity_pct": 42,
    }


async def _search_docs(ctx: ToolContext, query: str, limit: int = 5) -> dict:
    """Search knowledge base (mock)."""
    return {
        "query": query,
        "results": [
            {"title": f"Article {i + 1}", "snippet": f"Match for {query!r}…"}
            for i in range(min(limit, 3))
        ],
    }


# ---------------------------------------------------------------------------
# 2. Context-aware tool — reads ToolContext
# ---------------------------------------------------------------------------


async def _whoami(ctx: ToolContext) -> dict:
    """Return the current user identity from the chatbot's ToolContext.

    Useful for testing that the host framework's ``user_context`` callable is
    wired up correctly — switching frameworks should not change what this tool
    returns for the same logged-in user.
    """
    return {
        "user_id": ctx.user.id,
        "email": ctx.user.email,
        "metadata_keys": sorted(ctx.user.metadata.keys()),
        "conversation_id": ctx.conversation_id,
    }


# ---------------------------------------------------------------------------
# 3. Cached tool — second call within cache_ttl skips the body
# ---------------------------------------------------------------------------


async def _list_currencies(ctx: ToolContext) -> dict:
    """List supported currencies (cached for 5 minutes per user)."""
    return {
        "currencies": ["EUR", "USD", "GBP", "CHF", "JPY", "CAD", "AUD"],
        "served_from": "fresh body",  # would be swapped if served from cache_ttl
    }


# ---------------------------------------------------------------------------
# 4. Rate-limited tool — capped at N calls / minute / user
# ---------------------------------------------------------------------------


async def _rate_limited_ping(ctx: ToolContext) -> dict:
    """Trivial ping — capped at 5 invocations/minute per user."""
    return {"pong": True, "user_id": ctx.user.id}


# ---------------------------------------------------------------------------
# 5. Approval-required tool — UI must Approve before execution
# ---------------------------------------------------------------------------


async def _send_email(ctx: ToolContext, to: str, subject: str, body: str) -> dict:
    """Send an email — requires user approval in the chat UI."""
    return {"status": "sent", "to": to, "subject": subject}


# ---------------------------------------------------------------------------
# 6. Error-state tool — drives the UI error rendering
# ---------------------------------------------------------------------------


async def _simulate_failure(ctx: ToolContext, reason: str = "unknown") -> dict:
    """Always fails — demos error state in tool cards."""
    raise RuntimeError(f"Simulated failure: {reason}")


# ---------------------------------------------------------------------------
# 7. HTTP-only tool — declarative REST call, no pagination
# ---------------------------------------------------------------------------


@http_tool(
    method="GET",
    url="https://api.frankfurter.app/latest?from={base}&to={target}",
    timeout=10.0,
    retry=2,
)
async def _get_exchange_rate(ctx: ToolContext, base: str = "EUR", target: str = "USD") -> dict:
    """Fetch the latest exchange rate between two currencies (Frankfurter.app)."""


# ---------------------------------------------------------------------------
# 8. Paginated + HTTP-only stack — full real-world tool with zero body
# ---------------------------------------------------------------------------

_BNPP_FIELDS = (
    "fund_name", "fundname", "name", "isin", "currency", "ccy",
    "asset_class", "category", "share_class", "share_class_name", "domicile",
    "ytd", "nav", "perf_ytd", "perf_1y", "perf_3y",
)
_BNPP_ID_FIELDS = ("id", "fund_id", "isin", "ticker")
_BNPP_URL_TEMPLATE = (
    "https://api.bnpparibas-am.com/push/fundsearchv2/{profile}/{language}"
    "?without_has_docs=True&action_column_tool=fundpanorama"
)


@paginated(
    fields=_BNPP_FIELDS,
    id_fields=_BNPP_ID_FIELDS,
    max_field_chars=200,
    default_limit=25,
    max_limit=500,  # 500 is enough to return the BNP catalog (~324 funds) in one call
    request_args=("profile", "language"),
)
@http_tool(
    method="GET",
    url=_BNPP_URL_TEMPLATE,
    timeout=20.0,
    max_response_chars=None,  # @paginated handles projection + slicing
)
async def _bnpp_fund_search(
    ctx: ToolContext,
    profile: str = "PV_LU-FSE",
    language: str = "ENG",
) -> dict:
    """Search BNP Paribas AM funds.

    Args:
        profile: Country/platform profile (e.g. ``PV_LU-FSE``).
        language: Two-or-three-letter language code (e.g. ``ENG``).

    The URL template, HTTP fetch, retries, projection, slicing, and envelope
    are all driven by the decorator stack — this function has no body.
    """


# ---------------------------------------------------------------------------
# Registry assembly
# ---------------------------------------------------------------------------


def build_tools() -> ToolRegistry:
    """Return a populated ToolRegistry covering every decorator pattern.

    Same registry is consumed by the FastAPI, Flask, and Django variants.
    """
    tools = ToolRegistry()

    # 1. Plain mocks
    tools.register(_get_weather, name="get_weather")
    tools.register(_search_docs, name="search_docs")

    # 2. Context-aware
    tools.register(_whoami, name="whoami")

    # 3. Cached
    tools.register(_list_currencies, name="list_currencies", cache_ttl=300.0)

    # 4. Rate-limited
    tools.register(_rate_limited_ping, name="rate_limited_ping", rate_limit_per_user=5)

    # 5. Approval-required
    tools.register(_send_email, name="send_email", requires_approval=True)

    # 6. Error-state
    tools.register(_simulate_failure, name="simulate_failure")

    # 7. HTTP-only
    tools.register(_get_exchange_rate, name="get_exchange_rate")

    # 8. Paginated + HTTP stack
    tools.register(_bnpp_fund_search, name="bnpp_fund_search")

    return tools
