"""Tests for the @paginated decorator."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from chatbot import ToolRegistry, paginated
from chatbot.tools import http_tool
from chatbot.tools.pagination import (
    _largest_list_of_dicts,
    _project_item,
    _resolve_dotted_path,
    _resolve_items,
)


# ---------------------------------------------------------------------------
# Internals: list resolution
# ---------------------------------------------------------------------------


def test_dotted_path_simple():
    payload = {"data": {"results": [{"x": 1}, {"x": 2}]}}
    assert _resolve_dotted_path(payload, "data.results") == [{"x": 1}, {"x": 2}]


def test_dotted_path_jsonpath_prefix():
    payload = {"fonds": [{"isin": "A"}]}
    assert _resolve_dotted_path(payload, "$.fonds") == [{"isin": "A"}]


def test_dotted_path_dollar_root():
    payload = [{"a": 1}, {"a": 2}]
    assert _resolve_dotted_path(payload, "$") == [{"a": 1}, {"a": 2}]


def test_dotted_path_missing_returns_empty():
    payload = {"data": {}}
    assert _resolve_dotted_path(payload, "data.results") == []


def test_dotted_path_non_list_returns_empty():
    payload = {"data": "not a list"}
    assert _resolve_dotted_path(payload, "data") == []


def test_largest_list_of_dicts_picks_richest():
    payload = {
        "meta": [1, 2, 3],  # 3 scalars
        "funds": [{"isin": "A"}, {"isin": "B"}],  # 2 dicts
        "tags": [],
    }
    result = _largest_list_of_dicts(payload)
    assert result == [{"isin": "A"}, {"isin": "B"}]


def test_largest_list_falls_back_to_longest_when_no_dicts():
    payload = {"ids": [1, 2, 3, 4], "tags": ["x", "y"]}
    result = _largest_list_of_dicts(payload)
    assert result == [1, 2, 3, 4]


def test_resolve_items_callable():
    payload = {"weird": {"nested": [{"a": 1}]}}
    items = _resolve_items(payload, lambda p: p["weird"]["nested"])
    assert items == [{"a": 1}]


def test_resolve_items_auto_on_flat_list():
    items = _resolve_items([{"a": 1}, {"a": 2}], None)
    assert items == [{"a": 1}, {"a": 2}]


def test_resolve_items_auto_on_dict():
    payload = {"profile": "X", "fonds": [{"isin": "A"}, {"isin": "B"}, {"isin": "C"}]}
    items = _resolve_items(payload, None)
    assert items == [{"isin": "A"}, {"isin": "B"}, {"isin": "C"}]


# ---------------------------------------------------------------------------
# Internals: projection
# ---------------------------------------------------------------------------


def test_project_with_allowlist_keeps_only_listed_fields():
    item = {"isin": "FR001", "currency": "EUR", "raw": {"nested": "dropped"}, "noisy": "x" * 5000}
    out = _project_item(item, ("isin", "currency"), id_fields=(), max_field_chars=200)
    assert out == {"isin": "FR001", "currency": "EUR"}


def test_project_default_heuristic_keeps_small_scalars_only():
    item = {
        "isin": "FR001",
        "currency": "EUR",
        "nav": 12.5,
        "active": True,
        "history": [1, 2, 3],         # dropped: not a scalar
        "details": {"nested": "x"},     # dropped: not a scalar
    }
    out = _project_item(item, allowed_fields=None, id_fields=(), max_field_chars=200)
    assert out == {"isin": "FR001", "currency": "EUR", "nav": 12.5, "active": True}


def test_project_truncates_long_strings():
    item = {"description": "x" * 500}
    out = _project_item(item, ("description",), id_fields=(), max_field_chars=20)
    assert out["description"].endswith("…")
    assert len(out["description"]) == 20


def test_project_preserves_id_fields_even_when_not_in_allowlist():
    item = {"isin": "FR001", "currency": "EUR", "extra": "drop"}
    out = _project_item(item, ("currency",), id_fields=("isin",), max_field_chars=200)
    assert out == {"currency": "EUR", "isin": "FR001"}


def test_project_non_dict_passes_through():
    out = _project_item("hello", ("foo",), id_fields=(), max_field_chars=100)
    assert out == "hello"


# ---------------------------------------------------------------------------
# Signature injection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_signature_injects_offset_and_limit():
    @paginated()
    async def my_tool(ctx, profile: str = "PV_LU-FSE") -> list[dict]:
        return [{"i": i} for i in range(10)]

    sig = inspect.signature(my_tool)
    assert "offset" in sig.parameters
    assert "limit" in sig.parameters
    assert sig.parameters["offset"].default == 0
    assert sig.parameters["limit"].default == 25  # default_limit
    assert sig.parameters["offset"].annotation is int


@pytest.mark.asyncio
async def test_signature_keeps_original_params():
    @paginated()
    async def my_tool(ctx, profile: str = "PV_LU-FSE", language: str = "ENG") -> list:
        return []

    sig = inspect.signature(my_tool)
    assert "profile" in sig.parameters
    assert "language" in sig.parameters


@pytest.mark.asyncio
async def test_existing_offset_param_not_overridden():
    """If the user already declares offset, leave it as-is."""

    @paginated()
    async def my_tool(ctx, offset: int = 5) -> list:
        return []

    sig = inspect.signature(my_tool)
    assert sig.parameters["offset"].default == 5


@pytest.mark.asyncio
async def test_rejects_sync_function():
    with pytest.raises(TypeError, match="async"):

        @paginated()
        def my_tool(ctx) -> list:
            return []


# ---------------------------------------------------------------------------
# End-to-end via ToolRegistry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registry_includes_offset_limit_in_schema():
    """tools.register builds the schema from the wrapped signature, so the
    decorator's injected offset/limit must show up automatically."""
    tools = ToolRegistry()

    @tools.register
    @paginated(fields=("isin",))
    async def search(ctx, profile: str = "PV_LU-FSE") -> list[dict]:
        return [{"isin": f"FR{i:03d}"} for i in range(50)]

    schema = tools.get("search").parameters_schema
    props = schema["properties"]
    assert "offset" in props
    assert "limit" in props
    assert "profile" in props


@pytest.mark.asyncio
async def test_full_pagination_envelope():
    @paginated(fields=("isin", "ccy"), id_fields=("id",), default_limit=5, max_limit=10)
    async def search(ctx) -> dict:
        return {
            "meta": {"unrelated": "x"},
            "fonds": [
                {"id": i, "isin": f"FR{i:03d}", "ccy": "EUR", "noise": "drop me"}
                for i in range(23)
            ],
        }

    out = await search(ctx=None, offset=10, limit=5)
    assert out["total"] == 23
    assert out["offset"] == 10
    assert out["limit"] == 5
    assert out["returned"] == 5
    assert out["has_more"] is True
    assert len(out["items"]) == 5
    assert out["items"][0] == {"id": 10, "isin": "FR010", "ccy": "EUR"}
    assert "noise" not in out["items"][0]


@pytest.mark.asyncio
async def test_pagination_has_more_false_on_last_page():
    @paginated(fields=("a",), default_limit=10, max_limit=10)
    async def t(ctx) -> dict:
        return {"items": [{"a": i} for i in range(7)]}

    out = await t(ctx=None, offset=0, limit=10)
    assert out["total"] == 7
    assert out["returned"] == 7
    assert out["has_more"] is False


@pytest.mark.asyncio
async def test_pagination_clamps_limit_to_max():
    @paginated(default_limit=5, max_limit=10)
    async def t(ctx) -> list:
        return [{"i": i} for i in range(100)]

    out = await t(ctx=None, offset=0, limit=999)
    assert out["limit"] == 10
    assert out["returned"] == 10


@pytest.mark.asyncio
async def test_pagination_negative_offset_clamped_to_zero():
    @paginated(default_limit=3, max_limit=5)
    async def t(ctx) -> list:
        return [{"i": i} for i in range(10)]

    out = await t(ctx=None, offset=-7, limit=3)
    assert out["offset"] == 0
    assert [it["i"] for it in out["items"]] == [0, 1, 2]


@pytest.mark.asyncio
async def test_pagination_with_callable_items_path():
    @paginated(items_path=lambda p: p["nested"]["records"], fields=("name",))
    async def t(ctx) -> dict:
        return {"nested": {"records": [{"name": f"r{i}"} for i in range(4)]}}

    out = await t(ctx=None, offset=0, limit=10)
    assert out["total"] == 4
    assert [it["name"] for it in out["items"]] == ["r0", "r1", "r2", "r3"]


@pytest.mark.asyncio
async def test_pagination_with_dotted_path():
    @paginated(items_path="$.data.results", fields=("name",))
    async def t(ctx) -> dict:
        return {"data": {"results": [{"name": f"r{i}"} for i in range(3)]}}

    out = await t(ctx=None, offset=0, limit=10)
    assert out["total"] == 3
    assert out["items"] == [{"name": "r0"}, {"name": "r1"}, {"name": "r2"}]


@pytest.mark.asyncio
async def test_pagination_forwards_extra_scalars():
    @paginated(fields=("name",), extra_scalars=("profile", "language"))
    async def t(ctx) -> dict:
        return {
            "profile": "PV_LU-FSE",
            "language": "ENG",
            "items": [{"name": "x"}],
            "complex_object": {"dropped": True},
        }

    out = await t(ctx=None)
    assert out["profile"] == "PV_LU-FSE"
    assert out["language"] == "ENG"
    assert "complex_object" not in out


@pytest.mark.asyncio
async def test_pagination_flat_list_payload():
    @paginated(fields=("name",))
    async def t(ctx) -> list:
        return [{"name": "a"}, {"name": "b"}, {"name": "c"}]

    out = await t(ctx=None, offset=1, limit=10)
    assert out["total"] == 3
    assert out["items"] == [{"name": "b"}, {"name": "c"}]


@pytest.mark.asyncio
async def test_request_args_forwards_passed_kwarg():
    @paginated(fields=("name",), request_args=("profile",))
    async def t(ctx, profile: str = "PV_LU-FSE") -> list:
        return [{"name": "a"}]

    out = await t(ctx=None, profile="PV_FR-RET")
    assert out["profile"] == "PV_FR-RET"


@pytest.mark.asyncio
async def test_request_args_uses_default_when_arg_not_passed():
    """If the LLM doesn't pass the arg, the wrapped fn's default must still surface."""

    @paginated(fields=("name",), request_args=("profile", "language"))
    async def t(ctx, profile: str = "PV_LU-FSE", language: str = "ENG") -> list:
        return [{"name": "a"}]

    out = await t(ctx=None)
    assert out["profile"] == "PV_LU-FSE"
    assert out["language"] == "ENG"


@pytest.mark.asyncio
async def test_request_args_wins_over_extra_scalars_on_conflict():
    """When both name the same key, the call arg is authoritative."""

    @paginated(
        fields=("name",),
        request_args=("profile",),
        extra_scalars=("profile",),
    )
    async def t(ctx, profile: str = "from_arg") -> dict:
        return {"profile": "from_payload", "items": [{"name": "a"}]}

    out = await t(ctx=None)
    assert out["profile"] == "from_arg"


@pytest.mark.asyncio
async def test_request_args_skips_non_scalar_values():
    """Tools that take a dict/list arg shouldn't blow up the envelope."""

    @paginated(fields=("name",), request_args=("filters",))
    async def t(ctx, filters: dict | None = None) -> list:
        return [{"name": "a"}]

    out = await t(ctx=None, filters={"a": 1, "b": 2})
    assert "filters" not in out


@pytest.mark.asyncio
async def test_request_args_cannot_overwrite_reserved_envelope_keys():
    """Forwarding a call arg named 'total' must not clobber the core envelope."""

    @paginated(fields=("x",), request_args=("total",))
    async def t(ctx, total: int = 999) -> list:
        return [{"x": i} for i in range(3)]

    out = await t(ctx=None)
    assert out["total"] == 3  # real total, not the call arg


@pytest.mark.asyncio
async def test_request_args_silently_skips_unknown_names():
    """Names not present in the function sig are ignored, not raised."""

    @paginated(fields=("name",), request_args=("bogus",))
    async def t(ctx, profile: str = "x") -> list:
        return [{"name": "a"}]

    # Must not raise; "bogus" is just dropped.
    out = await t(ctx=None)
    assert "bogus" not in out


# ---------------------------------------------------------------------------
# Composition: @paginated + @http_tool
# ---------------------------------------------------------------------------


def test_compose_preserves_original_signature_through_http_tool():
    """@http_tool now preserves __signature__, so @paginated can see profile/language."""

    @paginated(fields=("name",), request_args=("profile",))
    @http_tool(method="GET", url="https://x.test/{profile}", max_response_chars=None)
    async def search(ctx, profile: str = "default") -> dict:
        """ignored body"""

    sig = inspect.signature(search)
    # All four should be visible on the outermost wrapper
    assert "profile" in sig.parameters
    assert "ctx" in sig.parameters
    assert "offset" in sig.parameters
    assert "limit" in sig.parameters


def test_compose_paginated_auto_disables_http_cap():
    """Stacking @paginated on @http_tool must null out max_response_chars."""

    @paginated(fields=("x",))
    @http_tool(method="GET", url="https://x.test", max_response_chars=60_000)
    async def search(ctx) -> dict:
        """ignored"""

    # Find the inner http config via __wrapped__ — fn one level below @paginated.
    inner = search.__wrapped__
    assert inner._chatbot_http_tool_config.max_response_chars is None
    assert search._wraps_http_tool is True


def test_compose_registry_schema_includes_all_params():
    """When registered, the LLM-facing schema must expose call args + offset/limit."""
    tools = ToolRegistry()

    @tools.register
    @paginated(fields=("name",), request_args=("profile",))
    @http_tool(method="GET", url="https://x.test/{profile}", max_response_chars=None)
    async def search(ctx, profile: str = "default") -> dict:
        """ignored"""

    props = tools.get("search").parameters_schema["properties"]
    assert "profile" in props
    assert "offset" in props
    assert "limit" in props


def test_compose_reversed_order_is_rejected():
    """@http_tool @paginated would silently ignore pagination; must error."""
    with pytest.raises(TypeError, match="@paginated.*ABOVE @http_tool"):

        @http_tool(method="GET", url="https://x.test")
        @paginated(fields=("name",))
        async def bad(ctx, profile: str = "x") -> dict:
            """ignored"""


@pytest.mark.asyncio
async def test_compose_end_to_end_with_mocked_httpx(monkeypatch):
    """End-to-end: paginated(@http_tool) fetches, projects, slices, envelopes."""
    import chatbot.tools.http as http_mod

    captured_urls: list[str] = []

    class _FakeResponse:
        def __init__(self, payload: Any) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            pass

        def json(self) -> Any:
            return self._payload

    class _FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, *exc: Any) -> None:
            pass

        def build_request(self, method: str, url: str, **kwargs: Any) -> Any:
            captured_urls.append(url)
            # Reuse httpx's real request type for compatibility with auth.apply().
            import httpx as _httpx

            return _httpx.Request(method, url)

        async def send(self, request: Any) -> _FakeResponse:
            return _FakeResponse(
                {
                    "fonds": [
                        {
                            "id": i,
                            "isin": f"FR{i:03d}",
                            "currency": "EUR",
                            "ytd": float(i),
                            "noise": "x" * 1000,  # would blow context if not projected
                        }
                        for i in range(40)
                    ]
                }
            )

    monkeypatch.setattr(http_mod.httpx, "AsyncClient", _FakeAsyncClient)

    @paginated(
        fields=("isin", "currency", "ytd"),
        id_fields=("id",),
        request_args=("profile",),
        default_limit=10,
        max_limit=20,
    )
    @http_tool(
        method="GET",
        url="https://x.test/funds/{profile}",
        retry=0,
        max_response_chars=None,
    )
    async def fund_search(ctx, profile: str = "PV_LU-FSE") -> dict:
        """ignored"""

    out = await fund_search(ctx=None, profile="PV_FR-RET", offset=5, limit=3)

    # URL templating still worked
    assert captured_urls == ["https://x.test/funds/PV_FR-RET"]

    # Envelope shape
    assert out["total"] == 40
    assert out["offset"] == 5
    assert out["limit"] == 3
    assert out["returned"] == 3
    assert out["has_more"] is True
    assert out["profile"] == "PV_FR-RET"  # from request_args

    # Projection actually applied — noise must be gone, ids preserved
    assert out["items"][0] == {"id": 5, "isin": "FR005", "currency": "EUR", "ytd": 5.0}
    assert "noise" not in out["items"][0]


@pytest.mark.asyncio
async def test_pagination_default_heuristic_when_fields_none():
    @paginated()  # fields=None
    async def t(ctx) -> list:
        return [
            {
                "id": 1,
                "name": "thing",
                "history": [1, 2, 3],
                "meta": {"nested": "x"},
            }
        ]

    out = await t(ctx=None)
    item = out["items"][0]
    assert item == {"id": 1, "name": "thing"}
