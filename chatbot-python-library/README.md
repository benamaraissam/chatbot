# chatbot

A framework-agnostic Python chatbot backend — multi-LLM, MCP-ready, tools API.
Drop into FastAPI, Flask, Django, or Starlette, or run as its own server.

> Full documentation: [docs/libraries/python.md](../docs/libraries/python.md)

## Install

```bash
# Minimal
pip install chatbot

# With a framework adapter (most common)
pip install "chatbot[fastapi]"

# Everything: Flask, Django, Starlette, Postgres, OpenAPI auto-import,
# LiteLLM, standalone server
pip install "chatbot[all]"
```

Optional extras: `fastapi`, `flask`, `django`, `starlette`, `postgres`,
`redis`, `openapi`, `litellm`, `server`. See `pyproject.toml`.

## Quickstart

### Library mode — inside an existing FastAPI app

```python
from fastapi import FastAPI
from chatbot import Chatbot
from chatbot.integrations.fastapi import mount

app = FastAPI()
bot = Chatbot(provider="anthropic", model="claude-3-5-sonnet")
mount(app, agent=bot, path="/api/chat")
```

The same `mount(...)` exists for Starlette. Flask uses `create_blueprint(bot)`,
Django uses a Channels consumer. See the docs for adapter-specific notes.

### SDK mode — no HTTP layer

```python
import asyncio
from chatbot import Chatbot

async def main():
    bot = Chatbot(provider="openai", model="gpt-4o-mini")
    reply = await bot.send("Hello!")
    print(reply.text)

    async for event in bot.stream("Tell me a joke"):
        print(event.event_type, event.to_payload())

asyncio.run(main())
```

### Standalone server

```bash
chatbot serve --config config.yaml.example --port 8000
```

## Environment

The library reads provider credentials from environment variables (or pass
them programmatically). A `.env` file in the working directory is picked
up automatically:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://my-deployment.openai.azure.com
```

See `.env.example` for the full list.

## Highlights

- **Multi-LLM** — Anthropic, OpenAI (and any OpenAI-compatible URL), Azure
  OpenAI, plus 100+ providers via LiteLLM. Switching providers is one
  config change.
- **Tools as first-class** — Python callables, `@http_tool` decorator,
  auto-import from OpenAPI specs, plus MCP servers (stdio / SSE / HTTP).
- **Per-user auth** — tools receive scoped OAuth tokens via the request's
  `ToolContext`.
- **Streaming + thinking** — token-by-token SSE; assistant "thinking"
  trace streams separately and surfaces in the UI as a collapsible block.
- **Multimodal** — text + image + file parts share one `MessagePart` shape
  end-to-end.
- **Storage backends** — in-memory, SQLite, Postgres (asyncpg).
- **Skills + prompts** — load reusable skill bundles and composable system
  prompts from disk.

## Wire protocol

Every adapter exposes one endpoint that speaks the same HTTP + SSE
protocol — see [`docs/wire-protocol.md`](../docs/wire-protocol.md) for the
exact schemas and SSE event flow.

## Examples

Nine runnable examples ship under [`examples/`](examples/):

- `01_library_mode.py` — pure SDK
- `02_web_apps/` — full FastAPI app with custom bot, tools, prompts, and a skill
- `05_with_http_tools.py` — `@http_tool` decorator
- `06_with_openapi_import.py` — generate tools from an OpenAPI spec
- `07_with_mcp.py` — talking to an MCP server
- `08_standalone_server.py` — `chatbot serve` in code
- `09_openai_custom_url.py` — custom OpenAI-compatible endpoint

## Tests

```bash
pytest -q                                      # all tests
pytest tests/test_chatbot.py -v                # one module
pytest --cov=chatbot --cov-report=term-missing # with coverage
```

Or run the unified coverage script from the repo root:

```bash
make -C coverage coverage-python
```

See [`docs/development/testing.md`](../docs/development/testing.md).

## Publishing

Tag-driven via GitHub Actions — push a `python-v0.X.Y` tag and the workflow
runs tests, builds, and publishes to PyPI using trusted publishing. See
[`docs/development/ci-cd.md`](../docs/development/ci-cd.md).

## License

MIT.
