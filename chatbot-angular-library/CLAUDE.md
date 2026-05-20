# CLAUDE.md — chatbot-angular-library

This file gives Claude Code (the official CLI from Anthropic) the project context
it needs to be productive in this Angular workspace. It is also a public record
of how Claude was used to design, build, and maintain this library.

## Project overview

`chatbot-angular` is an Angular 17 workspace that publishes an embeddable
chatbot library plus a `demo` application used during local development.

- Angular 17 (standalone components + signals where applicable)
- Built and packaged with `ng-packagr`
- Talks to the `chatbot` Python backend over HTTP + SSE
- Distributed on npm as `chatbot-angular`

## Repository map

```
projects/
  chatbot-angular/   # The publishable library
  demo/              # Local dev application that consumes the library
angular.json         # CLI workspace configuration
package.json         # Workspace-level scripts (build, demo, test)
```

## Conventions

- TypeScript strict mode, Angular style guide
- Standalone components — no NgModule unless you have a specific reason
- All public symbols live under `projects/chatbot-angular/src/public-api.ts`
- Styles use the demo's design tokens; do not hard-code colors

## How Claude was used in this repository

This library was built with the assistance of Claude (Anthropic) — specifically
Claude Sonnet and Claude Opus via Claude Code. The integration is configured
under `.claude/` in this directory:

- **Agents** (`.claude/agents/`) — specialized subagents for Angular component
  review and SSE streaming integration.
- **Skills** (`.claude/skills/`) — reusable procedures for building the
  library, wiring the demo app, and publishing to npm.
- **Hooks** (`.claude/hooks/` + `.claude/settings.json`) — automatic
  TypeScript typecheck and Angular build verification after edits.

If you are working on this project with Claude Code, start by reading the
files under `.claude/` — they describe the contracts Claude is expected to
respect when modifying this workspace.

## Commands Claude should know

```bash
# Install dependencies
npm install

# Build the library
npm run build

# Run the demo app on http://localhost:4200
npm run demo

# Run unit tests for the library
npm test
```
