# CLAUDE.md — chatbot-python-library

This file gives Claude Code (the official CLI from Anthropic) the project context
it needs to be productive in this repository. It is also a public record of how
Claude was used to design, build, and maintain this library.

## Project overview

`chatbot` is a framework-agnostic Python chatbot backend:

- Multi-LLM (Anthropic, OpenAI, Mistral, via `pydantic-ai`)
- MCP-ready (Model Context Protocol tool registry under `src/chatbot/mcp/`)
- Framework integrations: FastAPI, Flask, Django, Starlette (`src/chatbot/integrations/`)
- Pluggable storage backends (in-memory, Postgres, Redis) under `src/chatbot/storage/`
- Built-in tool runtime (`src/chatbot/tools/`) including a code interpreter
- Standalone server entrypoint: `chatbot serve --config config.yaml`

## Repository map

```
src/chatbot/
  core/            # Conversation, message, agent primitives
  integrations/    # FastAPI, Flask, ASGI, Django adapters
  mcp/             # MCP tool registry and client
  server/          # Standalone HTTP + SSE server
  storage/         # Memory / Postgres / Redis backends
  tools/builtin/   # Code interpreter and other shipped tools
tests/             # pytest suite (asyncio_mode = auto)
examples/          # Library-mode and standalone-server examples
```

## Conventions

- Python 3.11+, type-annotated, `pydantic` v2 models for IO
- Lint: `ruff` (line length 100, rules E/F/I/UP)
- Tests: `pytest` with `pytest-asyncio` in auto mode
- Public API stays minimal — anything in `chatbot.__init__` is part of the contract
- Optional dependencies are declared in `pyproject.toml` extras, never imported at module top level

## How Claude was used in this repository

This library was built with the assistance of Claude (Anthropic) — specifically
Claude Sonnet and Claude Opus via Claude Code. The integration is configured
under `.claude/` in this directory:

- **Agents** (`.claude/agents/`) — specialized subagents for Python testing,
  MCP integration review, and LLM-provider abstraction work.
- **Skills** (`.claude/skills/`) — reusable procedures for running the test
  suite, packaging the library, and authoring framework adapters.
- **Hooks** (`.claude/hooks/` + `.claude/settings.json`) — automatic `ruff`
  formatting on save and `pytest` on commit, so generated code stays consistent
  with the rest of the codebase.

If you are working on this project with Claude Code, start by reading the
files under `.claude/` — they describe the contracts Claude is expected to
respect when modifying this library.

## Commands Claude should know

```bash
# Install with all dev + framework extras
pip install -e ".[all]" && pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint / format
ruff check src/ tests/
ruff format src/ tests/

# Start the bundled server
chatbot serve --config config.yaml.example --port 8000
```
