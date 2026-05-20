# Chatbot Suite — Phased Development Plan

> A reverse-engineered, phased roadmap that retraces how the three libraries
> in this monorepo (`chatbot-python-library`, `chatbot-react-library`,
> `chatbot-angular-library`) were built, in the order they would have been
> built if we had followed this plan from day one.
>
> Each phase lists its **goal**, **deliverables (with file paths)**,
> **acceptance criteria**, and a rough **effort estimate** (S = ≤ 2 days,
> M = 3–5 days, L = 1–2 weeks).
>
> Built with the assistance of Claude (Anthropic). See each library's
> `CLAUDE.md` and `.claude/` directory for the agents, skills, and hooks
> we use during development.

---

## Vision

A portable React (and Angular) embeddable chatbot UI talking over a stable
HTTP + SSE wire protocol to a **framework-agnostic Python backend** that:

- Supports multiple LLM providers (Anthropic, OpenAI, Azure OpenAI, anything
  reachable through LiteLLM) behind a single async interface.
- Exposes tools as first-class citizens — Python callables, HTTP endpoints,
  OpenAPI specs, and MCP servers — all behind one registry.
- Plugs into FastAPI, Flask, Django, Starlette/ASGI, or runs as its own
  CLI-launched server.
- Can be embedded by any team in a few lines of code (a `<FloatingChatbot />`
  on the frontend, a `mount(app, agent=...)` call on the backend).

---

## Project tracks and dependencies

```
        ┌──────────────────────────────────────────┐
        │  Phase 0  Discovery & architecture       │
        └────┬─────────────────────────────────────┘
             │
        ┌────▼────────────────────────────────────┐
        │  Phase 1  Python core kernel             │
        └────┬────────────────────────────────────┘
             │
   ┌─────────┼───────────────────────────────┐
   ▼         ▼                               ▼
Phase 2  Phase 3                          Phase 4
Providers  Tools + MCP                    Skills/Prompts/Storage
   │         │                               │
   └────┬────┴───────────────────────────────┘
        ▼
   Phase 5  Framework integrations + standalone server
        │
        ▼
   Phase 6  Wire-protocol freeze  ◄──── consumed by Phase 7+9
        │
        ├──────────────────┐
        ▼                  ▼
   Phase 7-8 React      Phase 9-10 Angular
        │                  │
        └──────────┬───────┘
                   ▼
            Phase 11 Docs, examples, design system
                   ▼
            Phase 12 Release engineering & AI tooling (.claude/)
```

Phases 2, 3, and 4 are independent on top of Phase 1 and can be parallelised.
Phases 7–8 (React) and 9–10 (Angular) are independent once Phase 6 lands.

---

# Phase 0 — Discovery & architecture (effort: M)

**Goal.** Lock in the problem statement, the wire protocol, the public APIs of
each library, and the directory layout. No production code yet.

**Deliverables**

- `README.md` at repo root — what this monorepo contains and how to install
  each package.
- Architecture decision: **library-first** for the Python side (no closed
  server), **React first, Angular second** for the frontend, **SSE over
  HTTP** for streaming (no WebSocket).
- Wire-protocol sketch (later realised in Phase 6 as
  `src/chatbot/protocol/`) — message shape, SSE event names, tool-call
  representation, multimodal parts.
- Public-API sketch for each library:
  - Python: `Chatbot.send(...)`, `Chatbot.stream(...)`, `Agent`,
    `ToolRegistry`, `mount(app, agent=...)`.
  - React: `<ChatbotProvider>`, `<FloatingChatbot />`, `useChatbot()`.
  - Angular: `ChatbotService`, `<chatbot-floating />`, injection tokens.
- Repository layout decision: three sibling library folders, each with its
  own version and publish pipeline.

**Acceptance criteria**

- A diagram (in this file) clearly shows how the three libraries fit
  together.
- Every Phase 1+ task can point at a section of the wire-protocol sketch
  for its input/output contract.

---

# Phase 1 — Python core kernel (effort: L)

**Goal.** Stand up the smallest possible Python library that can hold a
conversation in memory using a fake LLM and emit a stream of events.

**Deliverables**

- `chatbot-python-library/pyproject.toml` — `hatchling` build, `chatbot`
  package, Python 3.11+, base deps (`pydantic-ai`, `httpx`, `tenacity`,
  `mcp`, `pydantic`), `ruff` and `pytest` dev deps, an `all` extra.
- `src/chatbot/__init__.py` — public re-exports.
- `src/chatbot/env.py` — environment-variable helpers (with `.env`
  support).
- `src/chatbot/core/__init__.py`
- `src/chatbot/core/events.py` — `Event` taxonomy: `MessageStart`,
  `TextDelta`, `ToolCallStart`, `ToolCallResult`, `MessageEnd`, `Error`.
- `src/chatbot/core/context.py` — `UserContext` (request-scoped, carries
  auth and per-user state).
- `src/chatbot/core/agent.py` — `AgentLoop` that drives provider →
  tool-call → provider until convergence or `max_tool_rounds`.
- `src/chatbot/core/chatbot.py` — `Chatbot` facade with `.send()` and
  `.stream()`.
- `src/chatbot/storage/base.py` — `Storage` abstract interface.
- `src/chatbot/storage/memory.py` — `InMemoryStorage` reference impl.
- `src/chatbot/providers/base.py` — `Provider` abstract interface.
- `src/chatbot/providers/mock.py` — deterministic mock provider used by
  tests.
- `tests/conftest.py` — shared fixtures.
- `tests/test_chatbot.py` — single-turn happy path.
- `tests/test_storage.py` — in-memory storage round-trips.

**Acceptance criteria**

- `pytest tests/test_chatbot.py tests/test_storage.py -v` is green.
- A single-turn conversation against the mock provider returns a streamed
  list of events ending in `MessageEnd`.
- `Chatbot.send()` works synchronously by exhausting `.stream()`.

---

# Phase 2 — LLM provider matrix (effort: L)

**Goal.** Implement real LLM providers behind the `Provider` interface and a
small URL/registry helper so users can point at custom endpoints (Azure,
self-hosted, proxies).

**Deliverables**

- `src/chatbot/providers/anthropic.py` — Claude provider, streaming,
  tool-use loop.
- `src/chatbot/providers/openai.py` — OpenAI / OpenAI-compatible provider.
- `src/chatbot/providers/openai_messages.py` — internal helper that
  converts the canonical `Message` model to OpenAI message format
  (text + tool calls + multimodal parts).
- `src/chatbot/providers/azure_openai.py` — Azure-flavoured wrapper over
  `openai.py` with deployment-name resolution.
- `src/chatbot/providers/litellm.py` — pass-through to `litellm` for the
  long tail of providers.
- `src/chatbot/providers/urls.py` — base-URL / custom-endpoint resolution.
- `src/chatbot/providers/mock_scenarios.py` — scripted mock provider that
  replays a list of canned responses (for e2e-style tests).
- `tests/test_openai_messages.py` — message-shape conversion is
  round-trippable.
- `tests/test_openai_stream.py` — streaming path emits the expected events.
- `tests/test_azure_openai.py` — endpoint resolution & request shape.
- `tests/test_providers_urls.py` — URL helpers (trailing slashes,
  overrides, env-var precedence).
- `tests/test_mock_scenarios.py` — scenarios run deterministically.
- `chatbot-python-library/.env.example` — documents `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`, `AZURE_OPENAI_*`, etc.

**Acceptance criteria**

- Same conversation script produces a green test against `mock`,
  `openai_messages` (mocked HTTP), and `azure_openai` (mocked HTTP).
- Switching providers is one config change; the agent loop is unchanged.

---

# Phase 3 — Tooling subsystem & MCP (effort: L)

**Goal.** Make tools first-class: register Python callables, generate tools
from HTTP/OpenAPI, and consume MCP servers — all behind a unified
`ToolRegistry`.

**Deliverables**

- `src/chatbot/tools/__init__.py`
- `src/chatbot/tools/registry.py` — `ToolRegistry`, schema generation from
  Python type hints, name collision handling.
- `src/chatbot/tools/auth.py` — per-user credential plumbing (OAuth
  tokens, scoped API keys) routed through `UserContext`.
- `src/chatbot/tools/http.py` — declarative HTTP tool (one method/URL,
  templated path/query/body).
- `src/chatbot/tools/openapi.py` — import an OpenAPI spec and generate one
  tool per operation.
- `src/chatbot/tools/pagination.py` — generic cursor/page/offset paginator
  used by HTTP tools that return lists.
- `src/chatbot/tools/builtin/__init__.py`
- `src/chatbot/tools/builtin/code_interpreter.py` — sandboxed Python
  execution tool.
- `src/chatbot/tools/builtin/web_search.py` — web search tool.
- `src/chatbot/tools/builtin/generate_file.py` — file-generation tool
  (returns a generated artifact reference).
- `src/chatbot/mcp/__init__.py`
- `src/chatbot/mcp/client.py` — MCP client supporting `stdio`, `sse`, and
  `http` transports.
- `src/chatbot/mcp/registry.py` — exposes MCP-discovered tools through the
  same `ToolRegistry` interface.
- `tests/test_tools.py` — registry, builtins, schema generation.
- `tests/test_agent_multi_tool.py` — agent loop chooses, calls, and chains
  multiple tools.
- `tests/test_max_tool_rounds.py` — runaway tool loops abort safely.
- `tests/test_pagination.py` — paginated HTTP tool returns concatenated
  pages with a stop signal.

**Acceptance criteria**

- Registering a Python function as a tool requires zero JSON Schema
  authoring — types and docstring are enough.
- An OpenAPI spec with N operations produces N tools, each individually
  callable and individually testable.
- An MCP server registered at startup adds its tools transparently.

---

# Phase 4 — Skills, prompts, persistent storage (effort: M)

**Goal.** Let users package reusable prompts and skill bundles, and persist
conversations beyond a single process.

**Deliverables**

- `src/chatbot/prompts/__init__.py`
- `src/chatbot/prompts/frontmatter.py` — parse `---` YAML frontmatter from
  prompt markdown files.
- `src/chatbot/prompts/registry.py` — load prompts from a directory and
  retrieve by name.
- `src/chatbot/skills/__init__.py`
- `src/chatbot/skills/frontmatter.py` — parse `SKILL.md` frontmatter.
- `src/chatbot/skills/registry.py` — discover skills under a directory,
  expose them to the agent.
- `src/chatbot/skills/load_tool.py` — load a tool declared inside a
  skill's directory.
- `src/chatbot/storage/sqlite.py` — file-backed storage for single-node
  deployments.
- `src/chatbot/storage/postgres.py` — async Postgres backend
  (`asyncpg`) for production.
- `tests/test_skills.py` — skill discovery + frontmatter validation.

**Acceptance criteria**

- A skill living under `examples/02_web_apps/skills/funds/SKILL.md` is
  discoverable and callable from the agent.
- Conversations survive a process restart when SQLite or Postgres storage
  is configured.
- Prompts are versioned files on disk — no hard-coded strings in code.

---

# Phase 5 — Framework integrations & standalone server (effort: L)

**Goal.** Drop the library into any Python web app, or run it as its own
server.

**Deliverables**

- `src/chatbot/integrations/__init__.py`
- `src/chatbot/integrations/_common.py` — shared helpers (request parsing,
  error mapping, SSE framing).
- `src/chatbot/integrations/asgi.py` — generic ASGI mount.
- `src/chatbot/integrations/fastapi.py` — `mount(app, agent=..., path=...)`
  wired to a FastAPI router.
- `src/chatbot/integrations/starlette.py` — Starlette equivalent.
- `src/chatbot/integrations/flask.py` — sync Flask blueprint.
- `src/chatbot/integrations/django.py` — Channels-based ASGI consumer.
- `src/chatbot/server/__init__.py`
- `src/chatbot/server/app.py` — bundled uvicorn app.
- `src/chatbot/server/config.py` — YAML config loader (matches
  `config.yaml.example`).
- `src/chatbot/cli.py` — `chatbot serve --config ... --port ...` entrypoint
  declared in `[project.scripts]`.
- `chatbot-python-library/config.yaml.example` — minimum working config.
- `tests/test_fastapi.py` — single-turn POST + SSE stream against an
  embedded FastAPI app using `httpx.AsyncClient`.

**Acceptance criteria**

- `chatbot serve --config config.yaml.example --port 8000` boots a working
  server that streams responses.
- Adding `from chatbot.integrations.fastapi import mount; mount(app, agent=...)`
  to a real FastAPI app is the entire integration.
- The Flask and Django adapters share the same wire contract; the React
  client cannot tell which is on the other end.

---

# Phase 6 — Wire-protocol freeze (effort: M)

**Goal.** Finalise the shared HTTP + SSE contract between backend and any
frontend, then freeze it. This is the contract Phases 7–10 build against.

**Deliverables**

- `src/chatbot/protocol/__init__.py`
- `src/chatbot/protocol/schemas.py` — `pydantic` models for `Message`,
  `MessagePart`, `ToolCall`, `ToolResult`, `Request`, `Response`.
- `src/chatbot/protocol/sse.py` — canonical SSE event names + serializer.
- `src/chatbot/protocol/multimodal.py` — image / file part shape, base64
  vs URL, MIME hints.
- `tests/test_protocol.py` — every schema round-trips JSON, every event
  shape is documented.
- `tests/test_multimodal.py` — image + text parts in a single message
  serialise and deserialise.

**Acceptance criteria**

- The schemas and SSE event names are the **only** thing the React and
  Angular clients depend on.
- A version field is included so future breaking changes can be detected.
- Schema files are referenced from the README so frontend devs can read
  them without opening Python source.

---

# Phase 7 — React library foundation (effort: M)

**Goal.** Stand up the React package, transport, store, and types — but no
UI components yet.

**Deliverables**

- `chatbot-react-library/package.json` — `chatbot-react` package,
  React 17 peer dep, peer deps marked optional where relevant
  (`shiki`), `files: ["dist"]`, `exports` map.
- `tsconfig.json`, `tsconfig.build.json`, `vite.config.ts` — library-mode
  vite build emitting ESM, UMD, CSS, and `.d.ts`.
- `tailwind.config.js`, `postcss.config.js`, `src/styles/tokens.css`,
  `src/styles/globals.css` — design tokens and Tailwind setup.
- `src/index.ts` — public entry, re-exports only.
- `src/types/protocol.ts` — TypeScript mirror of the Phase-6 schemas.
- `src/types/index.ts` — UI-side types (message, attachment, theme).
- `src/core/types.ts` — internal store types.
- `src/core/store.ts` — `zustand` store: messages, streaming state,
  config.
- `src/core/context.tsx` — React context for config + store.
- `src/core/ChatbotProvider.tsx` — top-level provider.
- `src/core/index.ts`
- `src/transport/sseClient.ts` — `fetch` + `ReadableStream` SSE consumer
  with `AbortController`.
- `src/transport/index.ts`
- `src/utils/id.ts`, `src/utils/storage.ts`, `src/utils/theme.ts`,
  `src/utils/primaryColor.ts`, `src/utils/thread.ts`,
  `src/utils/attachments.ts`, `src/utils/attachmentDisplay.ts`,
  `src/utils/messageParts.ts` — small, stand-alone helpers.

**Acceptance criteria**

- `npm run build` produces `dist/chatbot-react.js`,
  `dist/chatbot-react.umd.cjs`, `dist/chatbot-react.css`, and
  `dist/index.d.ts`.
- `npm run typecheck` is green.
- A bare `<ChatbotProvider>` mounted in the demo can hold state but does
  not yet render UI.

---

# Phase 8 — React UI components + hooks + demo (effort: L)

**Goal.** Build the embeddable UI on top of the foundation, plus a demo app
that exercises everything end-to-end.

**Deliverables**

- `src/hooks/useChatbot.ts` — top-level façade hook.
- `src/hooks/useConversation.ts` — read access to the messages list.
- `src/hooks/useStreamingChat.ts` — sending a message + listening to the
  stream.
- `src/hooks/index.ts`
- `src/components/FloatingButton.tsx`, `FloatingChatbot.tsx`,
  `ChatHeader.tsx`, `ChatWindow.tsx`, `ChatInput.tsx`,
  `MessageList.tsx`, `MessageBubble.tsx`, `AssistantTurn.tsx`,
  `PendingAssistantTurn.tsx`, `ThinkingIndicator.tsx`,
  `StreamingCursor.tsx`, `StreamingAnswerIndicator.tsx`,
  `MarkdownMessage.tsx`, `CodeBlock.tsx`, `CopyButton.tsx`,
  `BotAvatar.tsx`, `ToolCallCard.tsx`, `AttachmentImage.tsx`,
  `MessageAttachments.tsx`, `ComposerAttachments.tsx`.
- `src/components/index.ts`
- `demo/index.html`, `demo/main.tsx`, `demo/App.tsx`,
  `demo/DemoPage.tsx`, `demo/demo.css`, `demo/vite.config.ts`,
  `demo/vite-env.d.ts`.
- `chatbot-react-library/README.md` — install, peer deps, quickstart, npm
  publish steps.

**Acceptance criteria**

- `npm run dev` boots the demo on `http://localhost:5173` and a real
  conversation with the Python backend (Phase 5) streams to completion.
- Tool calls render as collapsible cards with input/output.
- Markdown messages render code blocks with copy buttons and highlighting
  (when `shiki` is installed).
- The library can be `npm pack`ed and dropped into a fresh React 17 or 18
  app with no extra configuration beyond importing the CSS.

---

# Phase 9 — Angular library foundation (effort: M)

**Goal.** Stand up an Angular 17 workspace that publishes `chatbot-angular`,
mirroring the React foundation feature-for-feature where it makes sense.

**Deliverables**

- `chatbot-angular-library/package.json`, `angular.json`,
  `tsconfig.json` — Angular 17 workspace.
- `projects/chatbot-angular/package.json`,
  `projects/chatbot-angular/ng-package.json`,
  `projects/chatbot-angular/tsconfig.lib.json`,
  `projects/chatbot-angular/tsconfig.lib.prod.json` — `ng-packagr`
  configuration.
- `projects/chatbot-angular/src/public-api.ts` — public surface.
- `projects/chatbot-angular/src/lib/types/protocol.ts`,
  `src/lib/types/index.ts` — TS mirror of the Phase-6 schemas (kept in
  sync with the React version).
- `projects/chatbot-angular/src/lib/tokens/chatbot-config.token.ts` —
  Angular DI token for runtime configuration.
- `projects/chatbot-angular/src/lib/services/chatbot.service.ts` —
  Angular service holding store + transport.
- `projects/chatbot-angular/src/lib/transport/sse-client.ts` — SSE
  client (same wire contract as React's).
- `projects/chatbot-angular/src/lib/utils/*.ts` — `id`, `storage`,
  `theme`, `primaryColor`, `thread`, `attachments`,
  `attachment-display`, `message-parts` — parallel to React utils.
- `projects/chatbot-angular/src/lib/styles/chatbot-angular.css` — base
  styles.

**Acceptance criteria**

- `npm run build` produces `dist/chatbot-angular/` with `fesm2022/`,
  `esm2022/`, type declarations, and `package.json` `exports`.
- `ng test chatbot-angular` runs (even with zero tests, scaffolding is
  correct).

---

# Phase 10 — Angular components + demo (effort: L)

**Goal.** Implement the parallel set of standalone Angular components and a
demo app, matching the React UI behavior.

**Deliverables**

- `projects/chatbot-angular/src/lib/components/floating-button/...`,
  `floating-chatbot/...`, `chat-header/...`, `chat-window/...`,
  `chat-input/...`, `message-list/...`, `message-bubble/...`,
  `assistant-turn/...`, `pending-assistant-turn/...`,
  `thinking-indicator/...`, `streaming-cursor/...`,
  `streaming-answer-indicator/...`, `markdown-message/...`,
  `copy-button/...`, `bot-avatar/...`, `tool-call-card/...`,
  `message-attachments/...`, `composer-attachments/...`.
  (Each component is a standalone `*.component.ts` file under its own
  folder.)
- `projects/demo/src/main.ts`, `projects/demo/src/index.html`,
  `projects/demo/src/styles.css`,
  `projects/demo/src/app/app.component.ts`,
  `projects/demo/src/app/app.config.ts`,
  `projects/demo/tsconfig.app.json`.
- `chatbot-angular-library/README.md` — install, peer deps, quickstart,
  npm publish steps.

**Acceptance criteria**

- `npm run demo` boots the Angular demo on `http://localhost:4200` and a
  real conversation against the Phase-5 backend streams correctly.
- Components are all standalone (no NgModules) and use OnPush change
  detection where they take inputs.
- The Angular demo and the React demo speak to the same Python backend
  using the same wire protocol.

---

# Phase 11 — Examples, documentation, design system (effort: M)

**Goal.** Make the project explorable by someone who has never seen it.

**Deliverables**

- `chatbot-python-library/examples/01_library_mode.py` — minimal "use as a
  library" example.
- `examples/02_web_apps/` — full FastAPI app showing a custom bot, tools,
  prompts, and skills:
  - `bot.py`
  - `fastapi_app.py`
  - `tools.py`
  - `prompts/system-prompt.md`
  - `skills/funds/SKILL.md`
  - `README.md` for the example.
- `examples/05_with_http_tools.py` — HTTP-tool registration.
- `examples/06_with_openapi_import.py` — OpenAPI auto-import.
- `examples/07_with_mcp.py` — talking to an MCP server.
- `examples/08_standalone_server.py` — `chatbot serve` in code.
- `examples/09_openai_custom_url.py` — pointing at a custom OpenAI
  endpoint (proxy, self-hosted).
- `chatbot-python-library/README.md` — install, configuration, integration
  recipes, publish-to-PyPI section.
- `chatbot-react-library/design-system/Chatbot React Design System.html`
  and `.pdf` — the UI design system reference.
- Repo-root `README.md` — index of the three libraries.

**Acceptance criteria**

- Every example runs from a clean checkout with a single `python <file>`
  (assuming credentials in `.env`).
- READMEs explain peer dependencies, optional extras, and publishing for
  each ecosystem.

---

# Phase 12 — Release engineering & AI tooling (effort: M)

**Goal.** Make releases low-risk and codify the workflow Claude follows
inside the repo.

**Deliverables**

- `chatbot-python-library/pyproject.toml` — `[project.optional-dependencies]`
  exhaustively cover the framework adapters; `all` extra rolls them up.
- React `package.json` + Angular `projects/chatbot-angular/package.json` —
  version, files, exports, peer-dep ranges.
- Repo-root `README.md` install/publish table.
- `.claude/` scaffolding in each library (this work — see also each
  library's `CLAUDE.md`):
  - `chatbot-python-library/.claude/agents/python-test-runner.md`,
    `mcp-integration-reviewer.md`
  - `chatbot-python-library/.claude/skills/run-tests/SKILL.md`,
    `add-framework-adapter/SKILL.md`
  - `chatbot-python-library/.claude/hooks/format-python.sh`,
    `run-tests.sh`
  - `chatbot-python-library/.claude/settings.json`
  - `chatbot-react-library/.claude/agents/react-component-reviewer.md`,
    `sse-streaming-specialist.md`
  - `chatbot-react-library/.claude/skills/build-library/SKILL.md`,
    `publish-to-npm/SKILL.md`
  - `chatbot-react-library/.claude/hooks/typecheck.sh`, `vite-build.sh`
  - `chatbot-react-library/.claude/settings.json`
  - `chatbot-angular-library/.claude/agents/angular-component-reviewer.md`,
    `sse-streaming-specialist.md`
  - `chatbot-angular-library/.claude/skills/build-and-test/SKILL.md`,
    `publish-to-npm/SKILL.md`
  - `chatbot-angular-library/.claude/hooks/typecheck.sh`, `ng-build.sh`
  - `chatbot-angular-library/.claude/settings.json`
- A `CLAUDE.md` at the root of each library documenting how Claude is
  used.

**Acceptance criteria**

- A new contributor running `claude` inside any library directory gets
  the right agents, skills, and hooks loaded automatically.
- `npm publish --dry-run` and `pip install -e ".[all]"` both work from
  fresh checkouts.
- Running Claude Code does not break the build: hooks no-op cleanly when
  their dependencies (`ruff`, `pytest`, `npm`) are unavailable.

---

## Backlog (post-Phase 12)

These items are intentionally not scheduled; they are candidates for v0.2+.

- Adapter for Litestar and Quart (`integrations/litestar.py`,
  `integrations/quart.py`) — uses the `add-framework-adapter` skill as a
  recipe.
- Vue 3 library (`chatbot-vue-library/`) — same wire contract, same UI
  surface, fourth sibling folder.
- A websocket transport behind a flag, for very-long-running tool calls.
- A `chatbot doctor` CLI command that validates an `.env` file, pings
  every configured provider, and prints the active tool registry.
- E2E tests across the three libraries running in CI against a real
  backend.

---

## How to use this plan

1. Phases should be picked up in order; intra-phase items can be parallelised.
2. Each phase ends with the listed acceptance criteria being green before
   the next phase starts.
3. When a phase is in progress, the `.claude/` agents and skills already
   in the repo can be used to scaffold and review the work.
4. If a deliverable's file path changes, update this plan in the same
   commit — the plan is the source of truth for what exists and why.
