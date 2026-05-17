"""Built-in web search tool (requires TAVILY_API_KEY or SERPER_API_KEY)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from chatbot.core.context import ToolContext
from chatbot.tools.registry import RegisteredTool


async def _web_search(ctx: ToolContext, query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the web for current information."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if api_key:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": max_results},
            )
            r.raise_for_status()
            return r.json().get("results", [])

    serper_key = os.environ.get("SERPER_API_KEY")
    if serper_key:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": serper_key},
                json={"q": query, "num": max_results},
            )
            r.raise_for_status()
            organic = r.json().get("organic", [])
            return [{"title": o.get("title"), "url": o.get("link"), "snippet": o.get("snippet")} for o in organic]

    raise ValueError("Set TAVILY_API_KEY or SERPER_API_KEY for web search")


web_search_tool = RegisteredTool(
    name="web_search",
    description="Search the web for current information on a topic.",
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5},
        },
        "required": ["query"],
    },
    fn=_web_search,
    timeout=15.0,
)
