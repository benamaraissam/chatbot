# Python backend — `chatbot-python-library`

A framework-agnostic Python library that hosts the agent loop and serves the
HTTP + SSE protocol. Ships on PyPI as `chatbot`.

> Source: [`chatbot-python-library/`](../../chatbot-python-library/) ·
> Library README: [`chatbot-python-library/README.md`](../../chatbot-python-library/README.md) ·
> Claude Code context: [`CLAUDE.md`](../../chatbot-python-library/CLAUDE.md)

## Install

```bash
# Minimal install
pip install chatbot

# With FastAPI adapter (most common)
pip install "chatbot[fastapi]"

# Everything — Flask, Django, Starlette, Postgres, Redis, OpenAPI, LiteLLM, server
pip install "chatbot[all]"
```

Optional extras declared in [`pyproject.toml`](../../chatbot-python-library/pyproject.toml):

| Extra | What it adds |
|---|---|
| `fastapi` | FastAPI + sse-starlette |
| `flask` | Flask |
| `django` | Django + Channels |
| `starlette` | Starlette + sse-starlette |
| `postgres` | `asyncpg` for the Postgres storage backend |
| `redis` | `redis-py` for cache and rate-limiting |
| `openapi` | `openapi-pydantic` for auto-generating tools from a spec |
| `litellm` | LiteLLM for the long tail of providers |
| `server` | `uvicorn` + `pyyaml` + `python-dotenv` for the standalone server |

## Package layout

```
src/chatbot/
├── __init__.py              # public re-exports
├── env.py                   # .env loader
├── cli.py                   # `chatbot` CLI entrypoint
├── core/
│   ├── chatbot.py           # Chatbot SDK facade
│   ├── agent.py             # AgentLoop — provider ↔ tool ↔ provider until convergence
│   ├── context.py           # UserContext, ToolContext, Secrets
│   └── events.py            # StreamEvent dataclasses (MessageStart, TextDelta, …)
├── providers/
│   ├── base.py              # Provider abstract interface
│   ├── anthropic.py         # Claude provider (httpx streaming)
│   ├── openai.py            # OpenAI / compatible
│   ├── openai_messages.py   # message-format converter for OpenAI
│   ├── azure_openai.py      # Azure deployment resolution
│   ├── litellm.py           # LiteLLM passthrough for everything else
│   ├── mock.py              # deterministic mock used in tests
│   ├── mock_scenarios.py    # scripted multi-turn scenarios
│   └── urls.py              # base-URL / endpoint resolution helpers
├── tools/
│   ├── registry.py          # ToolRegistry — typed dispatch + schema generation
│   ├── auth.py              # BearerAuth, OAuth2Auth, ApiKeyHeaderAuth
│   ├── http.py              # @http_tool decorator
│   ├── openapi.py           # from_openapi() — generate tools from a spec
│   ├── pagination.py        # @paginated decorator
│   └── builtin/             # code_interpreter, web_search, generate_file
├── mcp/
│   ├── client.py            # MCPClient — stdio / sse / http transports
│   └── registry.py          # MCPRegistry — aggregate multiple servers
├── skills/
│   ├── registry.py          # discover SKILL.md bundles under a directory
│   ├── frontmatter.py       # YAML frontmatter schema
│   └── load_tool.py         # load tools declared inside a skill
├── prompts/
│   ├── registry.py          # PromptRegistry — compose system prompts from .md files
│   └── frontmatter.py       # YAML frontmatter schema for prompts
├── protocol/
│   ├── schemas.py           # Pydantic models — Message, MessagePart, ChatRequest
│   ├── sse.py               # SSE codec + async iterator wrapper
│   └── multimodal.py        # provider_content_to_text + multimodal helpers
├── storage/
│   ├── base.py              # ConversationStorage abstract interface
│   ├── memory.py            # in-memory backend
│   ├── sqlite.py            # SQLite file backend
│   └── postgres.py          # asyncpg backend (extras=postgres)
├── integrations/
│   ├── _common.py           # request parsing, SSE framing, error mapping
│   ├── fastapi.py           # mount(app, agent=...) for FastAPI
│   ├── starlette.py         # same for Starlette
│   ├── flask.py             # create_blueprint(bot) for Flask
│   ├── django.py            # ASGI consumer (extras=django)
│   └── asgi.py              # generic ASGI mount
└── server/
    ├── app.py               # uvicorn app
    └── config.py            # YAML/JSON loader → ServerConfig

tests/                       # 27 pytest files (see development/testing.md)
examples/                    # nine runnable examples — see below
```

## Three integration modes

### A — Library mode in an existing FastAPI app

```python
from fastapi import FastAPI
from chatbot import Chatbot
from chatbot.integrations.fastapi import mount

app = FastAPI()
bot = Chatbot(provider="anthropic", model="claude-3-5-sonnet")
mount(app, agent=bot, path="/api/chat", sse=True)
```

That's it. The same `mount(...)` exists for Starlette. Flask uses
`create_blueprint(bot)`. Django uses a Channels consumer.

### B — Pure SDK (no HTTP layer)

```python
from chatbot import Chatbot

bot = Chatbot(provider="openai", model="gpt-4o-mini")

# Single turn (waits for completion)
reply = await bot.send("Hello!")
print(reply.text)

# Streaming
async for event in bot.stream("Hello!"):
    print(event.event_type, event.to_payload())
```

### C — Standalone server

```bash
chatbot serve --config config.yaml --port 8000
```

The CLI is declared in `[project.scripts]` and uses YAML config (see the
shipped [`config.yaml.example`](../../chatbot-python-library/config.yaml.example)).

## Providers

Every provider implements the same abstract interface
([`providers/base.py`](../../chatbot-python-library/src/chatbot/providers/base.py))
and emits the same `ProviderStreamChunk` shape. Switching providers is one
config change.

| Provider | Notes |
|---|---|
| `anthropic` | Native Claude API via httpx streaming |
| `openai` | OpenAI + any OpenAI-compatible endpoint (LiteLLM proxies, vLLM, Together, etc.) |
| `azure_openai` | Resolves Azure deployment names, supports AAD + API key |
| `litellm` | Pass-through for 100+ providers; install `chatbot[litellm]` |
| `mock` | Deterministic responses for tests |

Custom base URLs (proxies, internal gateways):

```python
Chatbot(provider="openai", model="gpt-4o", base_url="https://my-proxy.local/v1")
```

## Tools

Three ways to register a tool, all behind the same `ToolRegistry`:

```python
from chatbot import Chatbot
from chatbot.tools.http import http_tool
from chatbot.tools.openapi import from_openapi

bot = Chatbot(provider="anthropic", model="claude-3-5-sonnet")

# 1. Plain Python callable — schema generated from type hints + docstring
@bot.tools.tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

# 2. HTTP endpoint (declarative)
@http_tool(method="GET", url="https://api.example.com/weather/{city}")
async def get_weather(city: str, units: str = "metric") -> dict:
    """Fetch weather for a city."""

bot.tools.register(get_weather)

# 3. Auto-import from an OpenAPI spec
for tool in from_openapi(
    spec_path="api.openapi.json",
    base_url="https://api.example.com",
):
    bot.tools.register(tool)
```

Per-user auth flows through `ToolContext`:

```python
from chatbot.core.context import UserContext
from chatbot.tools.auth import OAuth2Auth

@http_tool(
    method="POST",
    url="https://slack.com/api/chat.postMessage",
    auth=OAuth2Auth(provider="slack"),
)
async def post_to_slack(channel: str, text: str) -> dict:
    """Post a message to Slack as the current user."""
```

The runtime looks up the Slack token via `ctx.user.oauth_token("slack")`,
so different users hit the same tool with different credentials.

## MCP servers

```python
from chatbot.mcp.registry import MCPRegistry, MCPServer

mcp = MCPRegistry([
    MCPServer(name="notion", url="https://notion.example.com/mcp"),
    MCPServer(name="local-tools", command=["mcp-server", "--port", "9000"]),
])
await mcp.connect_all()
await mcp.load_tools_into(bot.tools)
```

After `load_tools_into`, every MCP-exposed tool is callable through the
unified `ToolRegistry` with names like `mcp_notion_search_pages`.

## Skills and prompts

```
my-app/
├── prompts/
│   ├── system-prompt.md
│   └── finance-addendum.md
└── skills/
    └── funds/
        ├── SKILL.md
        ├── search.py
        └── data.csv
```

Each file starts with YAML frontmatter:

```markdown
---
name: base
description: Base assistant persona.
order: 0
---
You are a helpful financial-data assistant.
```

```python
from chatbot import PromptRegistry, Chatbot
from pathlib import Path

prompts = PromptRegistry.from_directory(Path("prompts/"))
bot = Chatbot(
    provider="anthropic",
    model="claude-3-5-sonnet",
    system_prompt=prompts.build_system_prompt(),
)
```

## Storage

```python
from chatbot.storage.sqlite import create_storage

storage = create_storage("sqlite:///./conversations.db")
bot = Chatbot(provider="anthropic", model="claude-3-5-sonnet", storage=storage)
```

`create_storage` dispatches by DSN scheme:

- `None` or `"memory"` → in-memory
- `"sqlite://..."` → SQLite file
- `"postgres://..."` → asyncpg (extras=postgres)

## Examples

Nine runnable examples ship under
[`chatbot-python-library/examples/`](../../chatbot-python-library/examples/):

| File | Demonstrates |
|---|---|
| `01_library_mode.py` | Plain SDK use, no HTTP layer |
| `02_web_apps/` | Full FastAPI app with custom bot, tools, prompts, and a skill |
| `05_with_http_tools.py` | `@http_tool` decorator |
| `06_with_openapi_import.py` | `from_openapi(spec_path=...)` |
| `07_with_mcp.py` | Talking to an MCP server |
| `08_standalone_server.py` | `chatbot serve` in code |
| `09_openai_custom_url.py` | Pointing at a self-hosted OpenAI-compatible endpoint |

## Testing

The Python library has 27 pytest files covering every subsystem. See
[development/testing.md](../development/testing.md) for the conventions and
how to add a new test.

```bash
pytest -q                         # everything, terse
pytest tests/test_tools.py -v     # one module
pytest -x --showlocals            # stop on first failure
```

## See also

- [Wire protocol](../wire-protocol.md) — what the HTTP layer speaks
- [Architecture](../architecture.md) — where this library sits in the stack
- [CI / CD](../development/ci-cd.md) — how this library publishes to PyPI
