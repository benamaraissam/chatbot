# Architecture

The system is three independently versioned libraries that share one wire
protocol. Each library does one thing well and nothing more.

## High-level view

```
┌───────────────────────────────────────────────────────────────────┐
│  Host application (any React, Angular, or vanilla web app)        │
│                                                                   │
│  ┌─────────────────────────┐    ┌─────────────────────────┐       │
│  │  chatbot-react          │ OR │  chatbot-angular        │       │
│  │  <ChatbotProvider>      │    │  ChatbotService         │       │
│  │  <FloatingChatbot/>     │    │  <cb-floating-chatbot/> │       │
│  └────────────┬────────────┘    └────────────┬────────────┘       │
│               │                              │                    │
└───────────────┼──────────────────────────────┼────────────────────┘
                │   HTTP + SSE (one protocol — same wire format)    │
                ▼                              ▼
   ┌───────────────────────────────────────────────────────┐
   │  Host Python application                              │
   │                                                       │
   │  ┌──────────────────────────────────────────────────┐ │
   │  │ Framework adapter (FastAPI, Flask, Django,       │ │
   │  │   Starlette/ASGI) — `mount(app, agent=...)`      │ │
   │  ├──────────────────────────────────────────────────┤ │
   │  │ Chatbot SDK   `Chatbot.send()` / `.stream()`     │ │
   │  ├──────────────────────────────────────────────────┤ │
   │  │ Agent loop · ToolRegistry · MCPClient · Providers│ │
   │  └──────────────────────────────────────────────────┘ │
   │                                                       │
   │      OR: `chatbot serve --config config.yaml`         │
   │      (standalone uvicorn server, same SDK underneath) │
   └───────────────────┬───────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────────┐
        ▼              ▼              ▼                  ▼
     Claude         OpenAI        Azure OpenAI      MCP servers
   (Anthropic)    (any URL)                       (stdio · sse · http)
                                                  + HTTP / OpenAPI tools
```

The frontends never talk to LLMs directly. Every model call goes through the
backend so credentials stay on the server side and the same business logic
applies across all clients.

## The three layers

### Backend — `chatbot-python-library`

A framework-agnostic Python library with four conceptual layers:

| Layer | Module | Responsibility |
|---|---|---|
| L1 — Core | `src/chatbot/core/` | Agent loop, events, conversation, user context |
| L2 — SDK | `src/chatbot/core/chatbot.py` | `Chatbot.send()` / `Chatbot.stream()` |
| L3 — Adapters | `src/chatbot/integrations/` | FastAPI, Flask, Django, Starlette, ASGI |
| L4 — Server | `src/chatbot/server/` + `cli.py` | Standalone uvicorn server with YAML config |

Plus orthogonal subsystems used by all layers:

- **Providers** (`src/chatbot/providers/`) — Anthropic, OpenAI, Azure OpenAI, LiteLLM, mock
- **Tools** (`src/chatbot/tools/`) — registry, builtin, HTTP, OpenAPI auto-import, pagination, auth
- **MCP** (`src/chatbot/mcp/`) — client + registry for Model Context Protocol servers
- **Skills** (`src/chatbot/skills/`) — package reusable skill bundles loaded from disk
- **Prompts** (`src/chatbot/prompts/`) — composable system prompts with YAML frontmatter
- **Storage** (`src/chatbot/storage/`) — in-memory, SQLite, Postgres backends
- **Protocol** (`src/chatbot/protocol/`) — schemas + SSE codec — see [wire-protocol.md](wire-protocol.md)

Detail: [libraries/python.md](libraries/python.md).

### React frontend — `chatbot-react-library`

Embeddable React components with a hooks-first API.

| Layer | Module | Responsibility |
|---|---|---|
| Provider | `src/core/ChatbotProvider.tsx` + `src/core/context.tsx` | Top-level config + store + send |
| State | `src/core/store.ts` (zustand) | Messages, streaming state, tool calls, attachments |
| Transport | `src/transport/sseClient.ts` | `fetch` + `ReadableStream` SSE consumer |
| Hooks | `src/hooks/` | `useChatbot`, `useChatbotActions`, `useStreamingChat`, `useConversation` |
| UI | `src/components/` | 20+ components: floating chatbot, chat window, header, messages, tool cards, attachments, markdown |
| Styling | `src/styles/`, `tailwind.config.js` | Design tokens + Tailwind utility CSS |

Detail: [libraries/react.md](libraries/react.md).

### Angular frontend — `chatbot-angular-library`

A standalone-components-only Angular 17 library with a signal-driven service.

| Layer | Module | Responsibility |
|---|---|---|
| DI | `projects/chatbot-angular/src/lib/tokens/chatbot-config.token.ts` | `CHATBOT_CONFIG` injection token |
| State | `projects/chatbot-angular/src/lib/services/chatbot.service.ts` | Signal-based store + `sendMessage()` |
| Transport | `projects/chatbot-angular/src/lib/transport/sse-client.ts` | Same SSE consumer pattern as React |
| UI | `projects/chatbot-angular/src/lib/components/` | Parallel set of components to React, ported one-to-one |

Detail: [libraries/angular.md](libraries/angular.md).

## What is shared, what is not

**Shared** (must stay in sync across all libraries):

- Wire protocol schemas (`protocol/schemas.py` ↔ `src/types/protocol.ts`)
- SSE event names (`message_start`, `text_delta`, `thinking_delta`, `tool_call_*`, `tool_result`, `message_end`, `error`, `done`)
- Design tokens (CSS variables: `--cb-primary`, `--cb-text`, `--cb-bg`, …)

**Not shared**:

- The agent loop, tool registry, and storage layer live only in Python.
- UI components are written natively per framework — there is no shared
  JS layer between React and Angular.

## Why this shape

- **Library-first** so users can drop it into existing apps without ceremony.
  Standalone server mode is an option, not the default.
- **One wire protocol** so a future Vue or Svelte port reuses the same
  protocol types without touching the backend.
- **Tools as first-class** so the model can take actions through a typed,
  permissioned, auditable surface — not free-text shell access.
- **MCP-native** so external tool servers (Notion, GitHub, Slack, in-house
  microservices) plug in without code changes.
- **Per-user auth** flowing through `ToolContext.user.oauth_token(...)` so
  one bot can safely serve many users.

## Cross-cutting concerns

- **Streaming**: every model call streams token-by-token via SSE so the UI
  shows progress before the full answer is ready.
- **Thinking trace**: reasoning text streams as `thinking_delta` separately
  from the user-visible answer, and lands on the assistant message as a
  collapsible trace.
- **Tool approval**: tools can require human-in-the-loop approval before
  execution via the `tool_approval_required` event.
- **Multimodal**: text + image + file parts share a single `MessagePart`
  shape end-to-end.

## See also

- [Wire protocol](wire-protocol.md) — exact schemas and SSE event details
- [Getting started](getting-started.md) — install and run in 5 minutes
- [Testing](development/testing.md) — how the three libraries are tested
- [`PLAN.md`](PLAN.md) — the phased roadmap that produced this codebase
