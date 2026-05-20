"""Tests for the @http_tool decorator and its response-capping behaviour."""
from __future__ import annotations

import json

import pytest

from chatbot.tools.http import http_tool


def test_http_tool_attaches_registration_metadata() -> None:
    @http_tool(method="GET", url="https://api.example.com/weather")
    async def get_weather(city: str) -> dict:
        """Fetch weather for a city."""

    # The decorator stores a RegisteredTool on the function for later
    # registration via registry.extend().
    assert hasattr(get_weather, "_chatbot_registered_tool")
    reg = get_weather._chatbot_registered_tool  # type: ignore[attr-defined]
    assert reg.name == "get_weather"
    assert "Fetch weather" in reg.description


def test_http_tool_uses_custom_name_when_provided() -> None:
    @http_tool(method="GET", url="https://api.example.com/items", name="list_items_v2")
    async def list_items() -> dict:
        """List items."""

    reg = list_items._chatbot_registered_tool  # type: ignore[attr-defined]
    assert reg.name == "list_items_v2"


def test_http_tool_rejects_wrapping_a_paginated_function() -> None:
    """@http_tool must be the *inner* decorator (@paginated wraps it on the outside)."""

    async def already_paginated(city: str) -> dict:
        """."""

    # Simulate the @paginated marker that lives outside the http_tool.
    already_paginated._paginated_config = object()  # type: ignore[attr-defined]

    with pytest.raises(TypeError, match="paginated"):
        http_tool(method="GET", url="x")(already_paginated)


# ─────────────────────────────────────────────────────────────────────────────
# Response capping (_cap_response is exercised through the decorator's behaviour;
# we re-import the helper here for direct, focused assertions).
# ─────────────────────────────────────────────────────────────────────────────


def test_cap_response_returns_payload_unchanged_when_under_limit() -> None:
    from chatbot.tools.http import _cap_response

    payload = {"items": [1, 2, 3]}
    assert _cap_response(payload, max_chars=1000) is payload


def test_cap_response_no_limit_passes_through() -> None:
    from chatbot.tools.http import _cap_response

    payload = {"x": "y" * 1_000_000}
    assert _cap_response(payload, max_chars=None) is payload


def test_cap_response_truncates_large_list_payload() -> None:
    from chatbot.tools.http import _cap_response

    payload = [{"i": i, "padding": "x" * 100} for i in range(1000)]
    capped = _cap_response(payload, max_chars=500)

    assert isinstance(capped, dict)
    assert capped["_truncated"] is True
    assert capped["total"] == 1000
    assert 0 < capped["returned"] < 1000
    # The hint mentions the truncation so the LLM knows to narrow filters.
    assert "truncat" in capped["_hint"].lower()


def test_cap_response_truncates_largest_list_inside_dict_payload() -> None:
    from chatbot.tools.http import _cap_response

    payload = {
        "page": 1,
        "items": [{"i": i} for i in range(1000)],
    }
    capped = _cap_response(payload, max_chars=200)

    assert isinstance(capped, dict)
    assert capped["_truncated"] is True
    # Shallow fields kept verbatim alongside the truncation envelope.
    assert capped.get("page") == 1
