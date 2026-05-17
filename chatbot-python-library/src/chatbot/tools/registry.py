"""Tool registry with registration, execution, rate limiting, and caching."""

from __future__ import annotations

import inspect
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, get_type_hints

from pydantic import BaseModel, create_model

from chatbot.core.context import ToolContext
from chatbot.core.events import ToolApprovalRequired

ToolCallable = Callable[..., Any]


@dataclass
class RegisteredTool:
    name: str
    description: str
    parameters_schema: dict[str, Any]
    fn: ToolCallable
    requires_approval: bool = False
    timeout: float = 30.0
    retry: int = 0
    cache_ttl: float | None = None
    rate_limit_per_user: int | None = None  # calls per minute


class ToolRegistry:
    """Registry of callable tools for the agent loop."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}
        self._cache: dict[str, tuple[float, Any]] = {}
        self._rate_counters: dict[str, list[float]] = {}

    def register(
        self,
        fn: ToolCallable | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        requires_approval: bool = False,
        timeout: float = 30.0,
        retry: int = 0,
        cache_ttl: float | None = None,
        rate_limit_per_user: int | None = None,
    ) -> Callable[[ToolCallable], ToolCallable] | ToolCallable:
        def decorator(f: ToolCallable) -> ToolCallable:
            tool_name = name or f.__name__
            tool_desc = description or (f.__doc__ or "").strip() or tool_name
            schema = _build_parameters_schema(f)
            self._tools[tool_name] = RegisteredTool(
                name=tool_name,
                description=tool_desc,
                parameters_schema=schema,
                fn=f,
                requires_approval=requires_approval,
                timeout=timeout,
                retry=retry,
                cache_ttl=cache_ttl,
                rate_limit_per_user=rate_limit_per_user,
            )
            return f

        if fn is not None:
            return decorator(fn)
        return decorator

    def extend(self, tools: list[RegisteredTool]) -> None:
        for tool in tools:
            self._tools[tool.name] = tool

    def get(self, name: str) -> RegisteredTool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[RegisteredTool]:
        return list(self._tools.values())

    def to_openai_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters_schema,
            }
            for t in self._tools.values()
        ]

    def to_anthropic_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters_schema,
            }
            for t in self._tools.values()
        ]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        ctx: ToolContext,
        *,
        approved: bool = False,
    ) -> Any | ToolApprovalRequired:
        tool = self.get(name)

        if tool.requires_approval and not approved:
            return ToolApprovalRequired(id=name, name=name, input=arguments)

        if tool.rate_limit_per_user:
            _check_rate_limit(self._rate_counters, f"{ctx.user.id}:{name}", tool.rate_limit_per_user)

        cache_key = None
        if tool.cache_ttl:
            cache_key = f"{name}:{json.dumps(arguments, sort_keys=True)}:{ctx.user.id}"
            cached = self._cache.get(cache_key)
            if cached and time.time() - cached[0] < tool.cache_ttl:
                return cached[1]

        result = await _execute_with_retry(tool, arguments, ctx)

        if cache_key and tool.cache_ttl:
            self._cache[cache_key] = (time.time(), result)

        return result

    def __len__(self) -> int:
        return len(self._tools)


async def _execute_with_retry(
    tool: RegisteredTool, arguments: dict[str, Any], ctx: ToolContext
) -> Any:
    from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

    async def _run() -> Any:
        return await _invoke_tool(tool, arguments, ctx)

    if tool.retry <= 0:
        return await _run()

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(tool.retry + 1),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
        reraise=True,
    ):
        with attempt:
            return await _run()
    raise RuntimeError("unreachable")


async def _invoke_tool(tool: RegisteredTool, arguments: dict[str, Any], ctx: ToolContext) -> Any:
    sig = inspect.signature(tool.fn)
    kwargs = dict(arguments)
    if "ctx" in sig.parameters:
        kwargs["ctx"] = ctx
    if inspect.iscoroutinefunction(tool.fn):
        return await tool.fn(**kwargs)
    return tool.fn(**kwargs)


def _build_parameters_schema(fn: ToolCallable) -> dict[str, Any]:
    hints = get_type_hints(fn)
    sig = inspect.signature(fn)
    fields: dict[str, Any] = {}
    for param_name, param in sig.parameters.items():
        if param_name == "ctx":
            continue
        annotation = hints.get(param_name, Any)
        default = ... if param.default is inspect.Parameter.empty else param.default
        fields[param_name] = (annotation, default)

    if not fields:
        return {"type": "object", "properties": {}}

    model = create_model(f"{fn.__name__}_params", **fields)  # type: ignore[call-overload]
    if issubclass(model, BaseModel):
        return model.model_json_schema()
    return {"type": "object", "properties": {}}


def _check_rate_limit(counters: dict[str, list[float]], key: str, limit: int) -> None:
    now = time.time()
    window = counters.setdefault(key, [])
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= limit:
        raise RuntimeError(f"Rate limit exceeded for {key}")
    window.append(now)
