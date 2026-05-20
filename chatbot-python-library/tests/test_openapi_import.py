"""Tests for chatbot.tools.openapi.from_openapi — tool generation from a spec."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from chatbot.tools.openapi import from_openapi


# Minimal but realistic OpenAPI 3.x fragment with three operations.
SAMPLE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Weather", "version": "1.0.0"},
    "paths": {
        "/weather/{city}": {
            "get": {
                "operationId": "get_weather",
                "summary": "Get current weather for a city.",
                "parameters": [
                    {"name": "city", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "units", "in": "query", "schema": {"type": "string"}},
                ],
            }
        },
        "/forecasts": {
            "post": {
                "operationId": "create_forecast",
                "summary": "Save a forecast.",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string"},
                                    "days": {"type": "integer"},
                                },
                                "required": ["city"],
                            }
                        }
                    }
                },
            }
        },
        "/health": {
            # Non-dict / extension-like entries must be ignored gracefully.
            "x-internal": True,
            "get": {
                "summary": "Health check.",
                # no operationId — must fall back to slugified method+path
            },
        },
    },
}


def test_generates_one_tool_per_operation() -> None:
    tools = from_openapi(spec=SAMPLE_SPEC, base_url="https://api.example.com")
    names = sorted(t.name for t in tools)
    # All three operations produce a tool. The /health get had no operationId
    # so the generator slugifies "get_/health" → "get__health".
    assert "get_weather" in names
    assert "create_forecast" in names
    assert any(n.startswith("get_") for n in names)
    assert len(tools) == 3


def test_path_parameter_marked_required_in_schema() -> None:
    tools = from_openapi(spec=SAMPLE_SPEC, base_url="https://api.example.com")
    by_name = {t.name: t for t in tools}
    schema = by_name["get_weather"].parameters_schema
    assert schema["type"] == "object"
    assert "city" in schema["properties"]
    assert "city" in schema["required"]
    # Optional query parameter is in properties but not required.
    assert "units" in schema["properties"]
    assert "units" not in schema["required"]


def test_request_body_schema_merged_into_parameters() -> None:
    tools = from_openapi(spec=SAMPLE_SPEC, base_url="https://api.example.com")
    by_name = {t.name: t for t in tools}
    schema = by_name["create_forecast"].parameters_schema
    assert "city" in schema["properties"]
    assert "days" in schema["properties"]
    assert "city" in schema["required"]


def test_include_filter_restricts_generated_tools() -> None:
    tools = from_openapi(
        spec=SAMPLE_SPEC,
        base_url="https://api.example.com",
        include=["get_weather"],
    )
    assert [t.name for t in tools] == ["get_weather"]


def test_exclude_filter_removes_matching_tools() -> None:
    tools = from_openapi(
        spec=SAMPLE_SPEC,
        base_url="https://api.example.com",
        exclude=["create_forecast"],
    )
    names = [t.name for t in tools]
    assert "create_forecast" not in names
    assert "get_weather" in names


def test_load_spec_from_disk(tmp_path: Path) -> None:
    p = tmp_path / "openapi.json"
    p.write_text(json.dumps(SAMPLE_SPEC), encoding="utf-8")
    tools = from_openapi(spec_path=str(p), base_url="https://api.example.com")
    assert len(tools) == 3


def test_load_spec_without_source_raises() -> None:
    with pytest.raises(ValueError, match="spec_url|spec_path|spec"):
        from_openapi(base_url="https://api.example.com")
