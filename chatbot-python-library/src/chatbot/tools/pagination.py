"""``@paginated`` decorator — slim large API responses, expose offset/limit to the LLM.

Wraps any async tool that returns a JSON-like payload containing a list of records
(e.g. an HTTP API result, a database query, an MCP tool). The decorator:

1. Injects ``offset: int = 0`` and ``limit: int`` parameters into the wrapped
   function's signature so the LLM can page on its own. The chatbot tool
   registry builds the JSON schema from the signature, so these show up
   automatically in the schema sent to the model.
2. Calls the original function with the LLM-supplied args (minus offset/limit).
3. Extracts the list of items from the payload via ``items_path`` (dotted path
   like ``"$.fonds"`` / ``"data.results"``, a callable, or autodetection that
   picks the largest list of dicts).
4. Projects each item to the configured ``fields`` allowlist (with optional
   per-field string truncation) and always preserves ``id_fields``. With
   ``fields=None`` the default behaviour is "keep small scalars".
5. Slices ``[offset : offset + limit]`` and wraps the result in a stable
   envelope: ``{total, offset, limit, returned, has_more, items, ...}``. Any
   top-level scalar fields from the original payload are preserved for context.

Use it **inside** ``@tools.register`` so the registered tool sees the
augmented signature::

    @tools.register
    @paginated(items_path="$.fonds", fields=("isin", "currency", "nav"))
    async def search_funds(ctx, profile: str = "PV_LU-FSE") -> dict:
        ...
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Iterable
from typing import Any

ItemsPath = str | Callable[[Any], list[Any]] | None

_DEFAULT_LIMIT = 25
_DEFAULT_MAX_LIMIT = 50
_DEFAULT_MAX_FIELD_CHARS = 200

_PRIMITIVE_TYPES = (str, int, float, bool)


def paginated(
    *,
    items_path: ItemsPath = None,
    fields: Iterable[str] | None = None,
    id_fields: Iterable[str] = ("id", "uid", "uuid", "key", "isin", "ticker"),
    max_field_chars: int = _DEFAULT_MAX_FIELD_CHARS,
    default_limit: int = _DEFAULT_LIMIT,
    max_limit: int = _DEFAULT_MAX_LIMIT,
    request_args: Iterable[str] | None = None,
    extra_scalars: Iterable[str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory — see module docstring for behaviour.

    Args:
        items_path: Where the list of records lives inside the payload.
            * ``None`` → auto-detect the largest ``list[dict]`` inside the payload.
              If the payload is itself a list it is used directly.
            * ``"data.results"`` / ``"$.fonds"`` → dotted path. Leading ``$.`` and
              ``$`` are optional.
            * ``callable(payload) -> list`` → arbitrary extractor.
        fields: Allowlist of fields to keep per item. ``None`` enables the
            small-scalar heuristic (keep top-level str/int/float/bool values that
            are short enough).
        id_fields: Identifier-like fields that are always preserved when present,
            in addition to ``fields``.
        max_field_chars: String values longer than this are truncated with ``…``.
        default_limit: Default page size when the LLM does not pass ``limit``.
        max_limit: Hard cap on ``limit`` (also clamps the LLM's request).
        request_args: Names of call kwargs to forward into the envelope so the
            LLM keeps request context (e.g. ``("profile", "language")``). Default
            parameter values from the wrapped function's signature are used when
            the LLM does not explicitly pass the arg. Non-scalar values are
            silently skipped. Reserved envelope keys (total, offset, limit,
            returned, has_more, items) are never overwritten.
        extra_scalars: Top-level keys from the **outer payload returned by the
            wrapped function** to forward into the envelope. Use this only when
            the upstream response itself carries useful context (e.g. an
            ``as_of_date`` computed server-side). For call-arg forwarding use
            ``request_args`` instead — it's almost always what you want.
    """
    allowed_fields = tuple(fields) if fields is not None else None
    id_field_tuple = tuple(id_fields)
    request_arg_tuple = tuple(request_args or ())
    extra_scalar_tuple = tuple(extra_scalars or ())
    default_limit = max(1, int(default_limit))
    max_limit = max(default_limit, int(max_limit))
    max_field_chars = max(1, int(max_field_chars))

    # Keys we never let request_args/extra_scalars overwrite.
    reserved = {"total", "offset", "limit", "returned", "has_more", "items"}

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(
                f"@paginated requires an async function; got sync function "
                f"{fn.__qualname__!r}. Wrap it as async or move @paginated inside "
                f"the async stack."
            )

        # If we're stacked on top of @http_tool, disable its built-in response
        # cap — @paginated is going to project + slice the payload, and the cap
        # would prematurely replace the list with a truncation marker.
        http_cfg = getattr(fn, "_chatbot_http_tool_config", None)
        if http_cfg is not None:
            http_cfg.max_response_chars = None

        original_sig = inspect.signature(fn)
        injected_sig = _augment_signature(original_sig, default_limit)

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            # Pull our injected args out before delegating to the wrapped fn.
            offset = max(0, int(kwargs.pop("offset", 0)))
            requested_limit = int(kwargs.pop("limit", default_limit))
            limit = max(1, min(requested_limit, max_limit))

            # Snapshot request_args values from the call (incl. defaults) before
            # delegating, so payload mutations can't influence what we forward.
            request_arg_values = _capture_request_args(
                fn, args, kwargs, request_arg_tuple
            )

            payload = await fn(*args, **kwargs)

            items = _resolve_items(payload, items_path)
            projected = [
                _project_item(it, allowed_fields, id_field_tuple, max_field_chars)
                for it in items
            ]
            page = projected[offset : offset + limit]

            envelope: dict[str, Any] = {
                "total": len(projected),
                "offset": offset,
                "limit": limit,
                "returned": len(page),
                "has_more": offset + len(page) < len(projected),
                "items": page,
            }

            # Forward call-arg context first (authoritative; wins over payload scalars).
            for key, value in request_arg_values.items():
                if key in reserved:
                    continue
                if isinstance(value, _PRIMITIVE_TYPES):
                    envelope.setdefault(key, value)

            # Forward selected scalar context from the outer payload, if any.
            if isinstance(payload, dict) and extra_scalar_tuple:
                for key in extra_scalar_tuple:
                    if key in reserved:
                        continue
                    if key in payload and isinstance(payload[key], _PRIMITIVE_TYPES):
                        envelope.setdefault(key, payload[key])

            return envelope

        wrapper.__signature__ = injected_sig  # type: ignore[attr-defined]
        # Update annotations so get_type_hints reports offset/limit too.
        wrapper.__annotations__ = {**fn.__annotations__, "offset": int, "limit": int}
        wrapper._paginated_config = {  # type: ignore[attr-defined]
            "items_path": items_path,
            "fields": allowed_fields,
            "id_fields": id_field_tuple,
            "max_field_chars": max_field_chars,
            "default_limit": default_limit,
            "max_limit": max_limit,
            "request_args": request_arg_tuple,
            "extra_scalars": extra_scalar_tuple,
        }
        wrapper._wraps_http_tool = http_cfg is not None  # type: ignore[attr-defined]
        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _capture_request_args(
    fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    names: tuple[str, ...],
) -> dict[str, Any]:
    """Resolve the named call args (including parameter defaults from ``fn``).

    Uses ``inspect.signature(fn).bind_partial`` so defaults declared on the
    wrapped function show up even when the LLM didn't pass them explicitly.
    Returns ``{name: value}`` for names that resolved to a value; silently
    skips names not present in the signature.
    """
    if not names:
        return {}
    try:
        bound = inspect.signature(fn).bind_partial(*args, **kwargs)
    except TypeError:
        # Mis-bound call — fall back to whatever's in kwargs directly.
        return {k: kwargs[k] for k in names if k in kwargs}
    bound.apply_defaults()
    return {k: bound.arguments[k] for k in names if k in bound.arguments}


def _augment_signature(sig: inspect.Signature, default_limit: int) -> inspect.Signature:
    """Return a copy of ``sig`` with ``offset`` and ``limit`` keyword params appended.

    Keyword-only placement ensures they don't collide with positional args the
    wrapped function already declared. If the function already declares
    ``offset`` or ``limit``, we leave the original parameter alone (the user is
    explicitly opting out of injection for that name).
    """
    params = list(sig.parameters.values())
    existing_names = {p.name for p in params}

    # If the function ends with **kwargs we have to insert before it.
    insert_at = len(params)
    for i, p in enumerate(params):
        if p.kind == inspect.Parameter.VAR_KEYWORD:
            insert_at = i
            break

    if "offset" not in existing_names:
        params.insert(
            insert_at,
            inspect.Parameter(
                "offset",
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=0,
                annotation=int,
            ),
        )
        insert_at += 1
    if "limit" not in existing_names:
        params.insert(
            insert_at,
            inspect.Parameter(
                "limit",
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=default_limit,
                annotation=int,
            ),
        )

    return sig.replace(parameters=params)


def _resolve_items(payload: Any, items_path: ItemsPath) -> list[Any]:
    """Find the list of records inside ``payload`` per the configured path."""
    if callable(items_path):
        result = items_path(payload)
        return list(result) if result is not None else []

    if isinstance(items_path, str):
        return _resolve_dotted_path(payload, items_path)

    # Auto-detect
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return _largest_list_of_dicts(payload)
    return []


def _resolve_dotted_path(payload: Any, path: str) -> list[Any]:
    """Walk a ``$.foo.bar`` / ``foo.bar`` path; return [] if missing or non-list."""
    cleaned = path.strip()
    if cleaned.startswith("$."):
        cleaned = cleaned[2:]
    elif cleaned == "$":
        cleaned = ""

    cursor: Any = payload
    if cleaned:
        for segment in cleaned.split("."):
            if not segment:
                continue
            if isinstance(cursor, dict) and segment in cursor:
                cursor = cursor[segment]
            else:
                return []
    if isinstance(cursor, list):
        return cursor
    return []


def _largest_list_of_dicts(payload: dict[str, Any]) -> list[Any]:
    """Find the largest list-of-dicts among the top-level values."""
    best: list[Any] = []
    best_dict_count = 0
    for value in payload.values():
        if isinstance(value, list):
            candidates = [v for v in value if isinstance(v, dict)]
            if len(candidates) > best_dict_count:
                best = candidates
                best_dict_count = len(candidates)
    if best_dict_count > 0:
        return best
    if not best:
        # Fall back to longest list of anything
        longest: list[Any] = []
        for value in payload.values():
            if isinstance(value, list) and len(value) > len(longest):
                longest = value
        best = longest
    return best


def _project_item(
    item: Any,
    allowed_fields: tuple[str, ...] | None,
    id_fields: tuple[str, ...],
    max_field_chars: int,
) -> Any:
    """Slim a single record per the projection rules."""
    if not isinstance(item, dict):
        # Non-dict items pass through as-is (caller may have a list of strings).
        return _truncate_value(item, max_field_chars)

    out: dict[str, Any] = {}
    if allowed_fields is None:
        # Heuristic: keep small scalars at the top level.
        for key, value in item.items():
            if isinstance(value, _PRIMITIVE_TYPES):
                out[key] = _truncate_value(value, max_field_chars)
    else:
        for key in allowed_fields:
            if key in item:
                value = item[key]
                if isinstance(value, _PRIMITIVE_TYPES):
                    out[key] = _truncate_value(value, max_field_chars)
                elif value is None:
                    out[key] = None
                else:
                    # Non-scalar allowed field: keep it but truncated as a string.
                    out[key] = _truncate_value(value, max_field_chars)

    # Always keep id-like fields if present and not already kept.
    for id_key in id_fields:
        if id_key in item and id_key not in out:
            value = item[id_key]
            if isinstance(value, _PRIMITIVE_TYPES):
                out[id_key] = _truncate_value(value, max_field_chars)

    return out


def _truncate_value(value: Any, max_chars: int) -> Any:
    if isinstance(value, str) and len(value) > max_chars:
        return value[: max_chars - 1] + "…"
    return value
