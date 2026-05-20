---
name: add-framework-adapter
description: Use when the user wants to add support for a new web framework (e.g., Sanic, Litestar, Quart) to chatbot. Walks through the adapter contract under src/chatbot/integrations/ and the extras pattern in pyproject.toml.
---

# Adding a framework adapter

The `chatbot` library is framework-agnostic. Each supported framework gets a
thin adapter module under `src/chatbot/integrations/` that wires the core
`Conversation` and `Agent` primitives to the framework's request/response
objects.

## Existing adapters

- `integrations/flask.py` — synchronous, blueprint-based
- `integrations/asgi.py` — generic ASGI mount, used by FastAPI and Starlette
- (Django uses Channels and lives under `integrations/django/`)

## Contract every adapter must expose

```python
def mount(app, *, agent, path: str = "/chat", sse: bool = True) -> None:
    """Attach a chat endpoint to the given app."""
```

Required behavior:
1. POST `<path>` accepts `{messages: [...], stream: bool}` and returns either a
   single JSON message or an SSE stream of `data: {...}\n\n` events.
2. Errors from the agent are surfaced as JSON `{error: {type, message}}` with
   appropriate HTTP status codes (`400` for client, `502` for upstream LLM).
3. The adapter must not import the underlying framework at module top level —
   import inside the function, so the extra stays optional.

## pyproject.toml extras

Add the framework to `[project.optional-dependencies]`:

```toml
mynewframework = ["mynewframework>=X.Y"]
```

And include it in the `all` extra.

## Tests

Add `tests/test_integration_<framework>.py` that uses the framework's test
client to POST a single-turn conversation and assert both streaming and
non-streaming behavior.
