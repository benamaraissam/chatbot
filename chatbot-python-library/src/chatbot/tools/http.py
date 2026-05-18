"""HTTP tool decorator — declarative REST API tools."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from chatbot.core.context import ToolContext
from chatbot.tools.auth import AuthScheme
from chatbot.tools.registry import RegisteredTool, ToolRegistry


@dataclass
class HttpTool:
    method: str
    url: str
    auth: AuthScheme | None = None
    timeout: float = 10.0
    retry: int = 3
    headers: dict[str, str] | None = None
    max_response_chars: int | None = None


def http_tool(
    *,
    method: str,
    url: str,
    auth: AuthScheme | None = None,
    timeout: float = 10.0,
    retry: int = 3,
    headers: dict[str, str] | None = None,
    name: str | None = None,
    requires_approval: bool = False,
    max_response_chars: int | None = 60_000,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that registers an HTTP-backed tool.

    ``max_response_chars`` caps the JSON-stringified response size that is sent
    back to the LLM. When the payload exceeds the cap, a truncation marker is
    returned instead so the model does not blow past its context window. Set
    to ``None`` to disable the safety net.
    """

    config = HttpTool(
        method=method,
        url=url,
        auth=auth,
        timeout=timeout,
        retry=retry,
        headers=headers,
        max_response_chars=max_response_chars,
    )

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        description = (fn.__doc__ or "").strip() or tool_name

        async def http_impl(ctx: ToolContext, **kwargs: Any) -> Any:
            resolved_url = _format_url(config.url, kwargs)
            request_kwargs = {k: v for k, v in kwargs.items() if f"{{{k}}}" not in config.url}

            async def _do_request() -> Any:
                async with httpx.AsyncClient(timeout=config.timeout) as client:
                    req = client.build_request(
                        config.method,
                        resolved_url,
                        params=request_kwargs if config.method.upper() == "GET" else None,
                        json=request_kwargs if config.method.upper() != "GET" else None,
                        headers=dict(config.headers or {}),
                    )
                    if config.auth:
                        await config.auth.apply(ctx, req)
                    response = await client.send(req)
                    response.raise_for_status()
                    return response.json()

            async def _run_with_retry() -> Any:
                if config.retry <= 0:
                    return await _do_request()
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(config.retry),
                    wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
                    reraise=True,
                ):
                    with attempt:
                        return await _do_request()
                raise RuntimeError("unreachable")

            result = await _run_with_retry()
            return _cap_response(result, config.max_response_chars)

        http_impl.__name__ = tool_name
        http_impl.__doc__ = description

        registered = RegisteredTool(
            name=tool_name,
            description=description,
            parameters_schema=_schema_from_url(config.url, fn),
            fn=http_impl,
            requires_approval=requires_approval,
            timeout=timeout,
            retry=0,
        )
        # Store for manual registration via registry.extend
        http_impl._chatbot_registered_tool = registered  # type: ignore[attr-defined]
        return http_impl

    return decorator


def register_http_tools(registry: ToolRegistry, *fns: Callable[..., Any]) -> None:
    """Register functions decorated with @http_tool."""
    tools = []
    for fn in fns:
        if hasattr(fn, "_chatbot_registered_tool"):
            tools.append(fn._chatbot_registered_tool)
        else:
            registry.register(fn)
    registry.extend(tools)


def _cap_response(payload: Any, max_chars: int | None) -> Any:
    """Return ``payload`` unchanged unless it serializes larger than ``max_chars``.

    Oversized payloads are replaced with a summary dict so the LLM sees the
    shape and a small preview without blowing past its context window. For
    list-shaped payloads (or dicts with a single large list value) the first
    items are kept so the model can still reason about the data.
    """
    if max_chars is None:
        return payload
    try:
        serialized = json.dumps(payload, default=str)
    except (TypeError, ValueError):
        return payload
    if len(serialized) <= max_chars:
        return payload

    # Try to keep a useful head of the data.
    if isinstance(payload, list):
        kept = _truncate_list(payload, max_chars)
        return {
            "_truncated": True,
            "_original_size_chars": len(serialized),
            "_max_response_chars": max_chars,
            "_hint": (
                "Response was truncated. "
                "Re-call the tool with narrower filters or pagination."
            ),
            "total": len(payload),
            "returned": len(kept),
            "items": kept,
        }
    if isinstance(payload, dict):
        # Find the longest list value and trim it.
        list_key = None
        max_len = 0
        for k, v in payload.items():
            if isinstance(v, list) and len(v) > max_len:
                max_len = len(v)
                list_key = k
        if list_key is not None:
            kept = _truncate_list(payload[list_key], max_chars)
            shallow = {k: v for k, v in payload.items() if k != list_key and _is_small(v)}
            return {
                "_truncated": True,
                "_original_size_chars": len(serialized),
                "_max_response_chars": max_chars,
                "_hint": (
                    f"Response was truncated. The '{list_key}' field had "
                    f"{len(payload[list_key])} items; returning the first {len(kept)}."
                ),
                **shallow,
                list_key: kept,
            }
    # Fallback: stringify and slice.
    return {
        "_truncated": True,
        "_original_size_chars": len(serialized),
        "_max_response_chars": max_chars,
        "_hint": "Response was truncated. Re-call the tool with narrower filters.",
        "preview": serialized[:max_chars],
    }


def _truncate_list(items: list[Any], max_chars: int) -> list[Any]:
    kept: list[Any] = []
    running = 2  # for "[]"
    for item in items:
        try:
            chunk = json.dumps(item, default=str)
        except (TypeError, ValueError):
            chunk = str(item)
        # +1 for comma separator
        if running + len(chunk) + 1 > max_chars:
            break
        kept.append(item)
        running += len(chunk) + 1
    return kept


def _is_small(value: Any, limit: int = 200) -> bool:
    try:
        return len(json.dumps(value, default=str)) <= limit
    except (TypeError, ValueError):
        return False


def _format_url(url_template: str, kwargs: dict[str, Any]) -> str:
    result = url_template
    for key, value in kwargs.items():
        result = result.replace(f"{{{key}}}", str(value))
    return re.sub(r"\{[^}]+\}", "", result)


def _schema_from_url(url: str, fn: Callable[..., Any]) -> dict[str, Any]:
    path_params = re.findall(r"\{(\w+)\}", url)
    import inspect
    from typing import get_type_hints

    hints = get_type_hints(fn)
    sig = inspect.signature(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name == "ctx":
            continue
        hint = hints.get(param_name, "string")
        json_type = "string"
        if hint in (int, float, bool):
            json_type = hint.__name__
        properties[param_name] = {"type": json_type, "description": param_name}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    for p in path_params:
        if p not in properties:
            properties[p] = {"type": "string"}
            required.append(p)

    return {"type": "object", "properties": properties, "required": required}
