"""Generate tools from OpenAPI specifications."""

from __future__ import annotations

import fnmatch
import json
import re
from typing import Any
from urllib.parse import urljoin

import httpx

from chatbot.core.context import ToolContext
from chatbot.tools.auth import AuthScheme, BearerAuth
from chatbot.tools.registry import RegisteredTool


def from_openapi(
    *,
    spec_url: str | None = None,
    spec_path: str | None = None,
    spec: dict[str, Any] | None = None,
    base_url: str,
    auth: AuthScheme | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    timeout: float = 30.0,
) -> list[RegisteredTool]:
    """
    Generate RegisteredTool instances from an OpenAPI 3.x spec.

    Requires: pip install chatbot[openapi]
    """
    openapi_spec = spec or _load_spec(spec_url, spec_path)
    paths = openapi_spec.get("paths", {})
    tools: list[RegisteredTool] = []

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId") or _slugify(f"{method}_{path}")
            pattern = f"{path}.{operation.get('operationId', method)}"
            if include and not any(fnmatch.fnmatch(pattern, p) for p in include):
                if not any(fnmatch.fnmatch(operation_id, p) for p in include):
                    continue
            if exclude and any(fnmatch.fnmatch(pattern, p) or fnmatch.fnmatch(operation_id, p) for p in exclude):
                continue

            tool = _operation_to_tool(
                operation_id=operation_id,
                method=method.upper(),
                path=path,
                operation=operation,
                base_url=base_url,
                auth=auth,
                timeout=timeout,
            )
            tools.append(tool)

    return tools


def _load_spec(spec_url: str | None, spec_path: str | None) -> dict[str, Any]:
    if spec_url:
        import httpx as hx

        response = hx.get(spec_url, timeout=60)
        response.raise_for_status()
        return response.json()
    if spec_path:
        with open(spec_path, encoding="utf-8") as f:
            return json.load(f)
    raise ValueError("Provide spec_url, spec_path, or spec dict")


def _operation_to_tool(
    *,
    operation_id: str,
    method: str,
    path: str,
    operation: dict[str, Any],
    base_url: str,
    auth: AuthScheme | None,
    timeout: float,
) -> RegisteredTool:
    description = operation.get("summary") or operation.get("description") or operation_id
    parameters = operation.get("parameters", [])
    request_body = operation.get("requestBody", {})

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in parameters:
        name = param.get("name", "")
        schema = param.get("schema", {"type": "string"})
        properties[name] = schema
        if param.get("required"):
            required.append(name)

    if request_body:
        content = request_body.get("content", {})
        json_schema = content.get("application/json", {}).get("schema", {})
        if json_schema.get("properties"):
            properties.update(json_schema["properties"])
            required.extend(json_schema.get("required", []))

    schema = {"type": "object", "properties": properties, "required": required}
    full_url_template = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

    async def openapi_impl(ctx: ToolContext, **kwargs: Any) -> Any:
        resolved_path = path
        for key, value in kwargs.items():
            resolved_path = resolved_path.replace(f"{{{key}}}", str(value))
        url = urljoin(base_url.rstrip("/") + "/", resolved_path.lstrip("/"))
        query_params = {
            k: v
            for k, v in kwargs.items()
            if f"{{{k}}}" not in path and k not in (request_body and properties or {})
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            req = client.build_request(
                method,
                url,
                params=query_params if method == "GET" else None,
                json={k: v for k, v in kwargs.items() if k in properties and f"{{{k}}}" not in path}
                if method != "GET"
                else None,
            )
            effective_auth = auth or BearerAuth(token_env="API_KEY")
            try:
                await effective_auth.apply(ctx, req)
            except ValueError:
                pass
            response = await client.send(req)
            response.raise_for_status()
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return response.text

    openapi_impl.__name__ = operation_id
    openapi_impl.__doc__ = description

    return RegisteredTool(
        name=operation_id,
        description=description,
        parameters_schema=schema,
        fn=openapi_impl,
        timeout=timeout,
    )


def _slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", value).strip("_")
