# CLAUDE.md — chatbot-react-library

This file gives Claude Code (the official CLI from Anthropic) the project context
it needs to be productive in this React library. It is also a public record of
how Claude was used to design, build, and maintain this package.

## Project overview

`chatbot-react` is an embeddable React chatbot component with SSE streaming.

- React 17+ (peer dep), TypeScript strict
- Vite for the library build, Vitest-compatible structure
- State: `zustand`; UI: `framer-motion`, `lucide-react`, `react-markdown` +
  `remark-gfm`, optional `shiki` for code highlighting
- Talks to the `chatbot` Python backend over HTTP + SSE
- Distributed on npm as `chatbot-react`

## Repository map

```
src/                 # Library source
demo/                # Vite-powered demo app (npm run dev)
design-system/       # Shared tokens and primitives
dist/                # Build output (generated)
vite.config.ts       # Library build config (tsc + vite)
tsconfig.build.json  # Types emit config
```

## Conventions

- TypeScript strict, no implicit any
- Components are functions, hooks-first; no class components
- Styles via Tailwind utility classes; `tailwind.config.js` is the source of truth
- Public exports live in `src/index.ts` — anything not exported there is internal
- Peer dependencies (`react`, `react-dom`) must never be imported transitively
  from a runtime dependency

## How Claude was used in this repository

This library was built with the assistance of Claude (Anthropic) — specifically
Claude Sonnet and Claude Opus via Claude Code. The integration is configured
under `.claude/` in this directory:

- **Agents** (`.claude/agents/`) — specialized subagents for React component
  review, accessibility, and SSE/streaming logic.
- **Skills** (`.claude/skills/`) — reusable procedures for building the
  library, running the demo, and publishing to npm.
- **Hooks** (`.claude/hooks/` + `.claude/settings.json`) — automatic
  TypeScript typecheck after edits and a full build before completion.

If you are working on this project with Claude Code, start by reading the
files under `.claude/` — they describe the contracts Claude is expected to
respect when modifying this library.

## Commands Claude should know

```bash
# Install
npm install

# Run the demo against the local source
npm run dev   # http://localhost:5173

# Type-check
npm run typecheck

# Build the library (output: dist/)
npm run build
```
