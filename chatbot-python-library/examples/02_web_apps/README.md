# Example 02 — FastAPI, Flask & Django sharing one bot

One example, three framework entry points, **one shared `bot.py` + `tools.py`**.
Switching frameworks does not change behaviour — the same provider config and
the same tools are served on every variant.

## Layout

| File              | Role |
|-------------------|------|
| `tools.py`        | `build_tools()` — every tool-authoring style the library supports (8 tools, see below). |
| `bot.py`          | `build_bot(tools)` — provider stack (mock / openai / azure / claude), default selection, system prompt, storage, all driven by env vars. |
| `fastapi_app.py`  | FastAPI variant: `app = FastAPI(); app.include_router(create_router(bot, ...))`. |
| `flask_app.py`    | Flask variant: `app = Flask(__name__); app.register_blueprint(create_blueprint(bot, ...))`. |
| `django_app.py`   | Django variant: single-file ASGI with `settings.configure(...)` + `chatbot_urls(...)`. |

## Run

```bash
# FastAPI on :8000
python examples/02_web_apps/fastapi_app.py

# Flask on :5000 (dev only — see file docstring for production SSE notes)
python examples/02_web_apps/flask_app.py

# Django on :8001 (single-file ASGI via uvicorn)
python examples/02_web_apps/django_app.py
```

All three expose `POST /api/chat/chat` (SSE) and `GET /` (health/discovery).

## Tools demonstrated

The same registry is used by every variant. Each tool exercises a different
library feature:

| Tool                | Demonstrates |
|---------------------|--------------|
| `get_weather`       | Plain `@tools.register` — async function with type hints. |
| `search_docs`       | Plain registration with a configurable `limit` arg. |
| `whoami`            | Context-aware: reads `ctx.user.id`, `ctx.user.email`, `ctx.conversation_id`. |
| `list_currencies`   | `cache_ttl=300` — repeated calls within 5 min skip the body per user. |
| `rate_limited_ping` | `rate_limit_per_user=5` — caps QPS per user. |
| `send_email`        | `requires_approval=True` — the React UI must Approve before execution. |
| `simulate_failure`  | Always raises — drives the UI error rendering. |
| `get_exchange_rate` | `@http_tool` standalone — declarative REST with URL templating + retry. |
| `bnpp_fund_search`  | `@paginated @http_tool` stack — fetch, project, slice, envelope, all in decorators; **no function body**. |

## Provider selection

`bot.py` registers a provider only if its credentials are present in the
environment, so the example boots end-to-end with zero config (mock provider).
Set `CHATBOT_DEFAULT_PROVIDER` to one of `mock` / `openai` / `azure` / `claude`
to pick the active one.

See the root `.env.example` for the full variable list and explanations.

## Auth integration

Each variant exposes a `get_user_context()` stub that returns a fixed user.
Replace it with your framework's current-user lookup:

- **FastAPI** — `def get_user_context(user = Depends(current_user)): return {"user_id": user.id, ...}`
- **Flask** — wrap with `@login_required` and read `flask_login.current_user`.
- **Django** — `request.user` is already injected; read `request.user.id`.

The `user_context` value flows into every tool call via `ToolContext`, so the
`whoami` tool above lets you verify the wiring works the same way across all
three frameworks.
