# Chatbot Suite — Documentation

A portable React (and Angular) embeddable chatbot UI talking to a
framework-agnostic Python backend over a stable HTTP + SSE protocol.

This is the documentation hub. The libraries themselves live one level up:

| Library | Path | Package |
|---|---|---|
| Backend | [`chatbot-python-library/`](../chatbot-python-library/) | PyPI · `chatbot` |
| React | [`chatbot-react-library/`](../chatbot-react-library/) | npm · `chatbot-react` |
| Angular | [`chatbot-angular-library/`](../chatbot-angular-library/) | npm · `chatbot-angular` |

## Read in this order

If you are new to the project, read the docs in this sequence:

1. [Architecture](architecture.md) — the big picture and the three layers
2. [Getting started](getting-started.md) — install + run the demo in 5 minutes
3. [Wire protocol](wire-protocol.md) — the HTTP + SSE contract every client speaks
4. The library guide for the stack you care about:
   - [Python backend](libraries/python.md)
   - [React frontend](libraries/react.md)
   - [Angular frontend](libraries/angular.md)
5. [Contributing](contributing.md) — how to make changes

## Topic index

### For users

- [Architecture](architecture.md)
- [Getting started](getting-started.md)
- [Wire protocol](wire-protocol.md) — message schema, SSE event names, multimodal parts
- [Python backend guide](libraries/python.md) — providers, tools, MCP, integrations, server
- [React library guide](libraries/react.md) — `ChatbotProvider`, hooks, components, theming
- [Angular library guide](libraries/angular.md) — `ChatbotService`, components, DI tokens

### For contributors

- [Testing](development/testing.md) — what runs where, how to write a new test
- [CI / CD](development/ci-cd.md) — pull-request checks and tag-driven releases
- [Claude in development](development/claude.md) — how Claude is used to build and maintain this codebase
- [Contributing](contributing.md) — workflow, code style, review process

### Reference materials

- [`PLAN.md`](PLAN.md) — the phased development roadmap
- Per-library CLAUDE.md files describe each library to Claude Code:
  - [`chatbot-python-library/CLAUDE.md`](../chatbot-python-library/CLAUDE.md)
  - [`chatbot-react-library/CLAUDE.md`](../chatbot-react-library/CLAUDE.md)
  - [`chatbot-angular-library/CLAUDE.md`](../chatbot-angular-library/CLAUDE.md)

## What this project is — in one paragraph

A backend Python library you drop into FastAPI, Flask, Django, Starlette, or
run as its own server. It speaks to any LLM (Anthropic, OpenAI, Azure,
or anything LiteLLM supports), exposes tools as first-class citizens
(Python callables, HTTP endpoints, OpenAPI auto-import, MCP servers), and
streams responses over HTTP + SSE. The frontend libraries (React and Angular)
share design tokens and consume the same SSE protocol — so they look
identical and behave identically regardless of which framework hosts them.

## What this project is _not_

- Not a closed-source SaaS — every layer is a library you control.
- Not a wrapper around one LLM — provider-agnostic by design.
- Not coupled to Next.js, NestJS, or any single framework — the adapters
  are thin and optional.
