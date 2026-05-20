# Claude in development

Claude (Anthropic) is used as a development partner across the three
libraries. This page describes the conventions that make that productive
and reproducible.

## The four touchpoints

1. **`CLAUDE.md`** at the root of each library — project context that
   Claude Code reads automatically when you `cd` into a library and run
   `claude`.
2. **`.claude/agents/`** — specialised subagents, invoked by name or
   proactively when they match the task.
3. **`.claude/skills/`** — procedural recipes auto-loaded based on
   trigger phrases in the request.
4. **`.claude/hooks/`** + `.claude/settings.json` — automatic checks that
   run after Claude edits a file (lint/typecheck) and after a turn
   completes (build/tests).

Everything lives inside the library directory it applies to, so you only
load what's relevant to where you're working.

## Per-library setup

### Python (`chatbot-python-library/.claude/`)

```
.claude/
├── settings.json
├── agents/
│   ├── python-test-runner.md         # runs pytest, surfaces failures, proposes fixes
│   ├── mcp-integration-reviewer.md   # reviews changes under mcp/ + tools/
│   └── test-author.md                # drafts new pytest tests
├── skills/
│   ├── run-tests/SKILL.md            # how to run the suite, conventions
│   ├── write-tests/SKILL.md          # patterns and file placement
│   └── add-framework-adapter/SKILL.md # how to add a new framework integration
└── hooks/
    ├── format-python.sh              # PostToolUse: ruff format + ruff check --fix
    └── run-tests.sh                  # Stop: pytest -q --maxfail=1
```

### React (`chatbot-react-library/.claude/`)

```
.claude/
├── settings.json
├── agents/
│   ├── react-component-reviewer.md   # standalone-pure-function patterns, a11y, memoisation
│   ├── sse-streaming-specialist.md   # SSE consumer correctness
│   └── test-author.md                # drafts new Vitest tests
├── skills/
│   ├── build-library/SKILL.md        # vite build + typecheck flow
│   ├── publish-to-npm/SKILL.md       # release steps
│   └── write-tests/SKILL.md          # Vitest patterns
└── hooks/
    ├── typecheck.sh                  # PostToolUse: tsc --noEmit
    └── vite-build.sh                 # Stop: npm run build
```

### Angular (`chatbot-angular-library/.claude/`)

```
.claude/
├── settings.json
├── agents/
│   ├── angular-component-reviewer.md # standalone components, signal idioms, OnPush
│   ├── sse-streaming-specialist.md   # SSE consumer correctness
│   └── test-author.md                # drafts new Karma/Jasmine specs
├── skills/
│   ├── build-and-test/SKILL.md       # ng build + ng test workflow
│   ├── publish-to-npm/SKILL.md       # release steps
│   └── write-tests/SKILL.md          # TestBed + signal patterns
└── hooks/
    ├── typecheck.sh                  # PostToolUse: tsc --noEmit on .ts edits
    └── ng-build.sh                   # Stop: npm run build
```

## How to use Claude Code in this repo

Install Claude Code (see [docs.claude.com](https://docs.claude.com/) for the
current command). Then, from inside any library:

```bash
cd chatbot-python-library
claude
```

The agents, skills, and hooks declared under `.claude/` activate
automatically. The `CLAUDE.md` is read into the session as context.

Example prompts that hit specific subagents / skills:

| You say | What activates |
|---|---|
| "Add a test for `prompts/registry.py`" | `test-author` agent + `write-tests` skill |
| "Run the tests and tell me what's failing" | `python-test-runner` agent + `run-tests` skill |
| "Review the MCP changes I just made" | `mcp-integration-reviewer` agent |
| "Add a Sanic adapter" | `add-framework-adapter` skill |
| "Build and pack the library" | `build-library` skill (React) / `build-and-test` skill (Angular) |

## Hook behaviour

`PostToolUse` hooks run after each `Edit` or `Write` operation. They are
designed to **degrade gracefully**: if the underlying tool (ruff, tsc,
ng) is not installed, the hook exits 0 and Claude proceeds. Failures
are surfaced as feedback to the next turn, not as hard errors that block
the session.

`Stop` hooks run once at the end of an assistant turn. They confirm the
test suite or build still passes, so a regression introduced during the
turn is visible immediately rather than at the next CI run.

## What Claude is *not* allowed to do

The `settings.json` `permissions.deny` block in each library blocks edits
to `.venv/`, `node_modules/`, `.env`, lockfiles, and `dist/`. Tests will
never be silently disabled or skipped — that's an explicit guardrail in
every `test-author` and `*-test-runner` agent prompt.

## Adding your own agent or skill

Drop a new markdown file under `.claude/agents/` or `.claude/skills/<name>/`
with YAML frontmatter:

```markdown
---
name: my-helper
description: One-sentence trigger description. Triggers include "X", "Y".
tools: Read, Edit, Bash
model: sonnet
---

# Body — the system prompt for the subagent
```

For skills, the convention is `.claude/skills/<name>/SKILL.md` and the
description doubles as the trigger. Be specific so it activates on the
right requests and stays out of the way otherwise.

## See also

- [Testing](testing.md) — what the hooks check on every edit
- [CI / CD](ci-cd.md) — the human-side checks that mirror what Claude runs locally
- [Architecture](../architecture.md) — the layout these tools target
- Anthropic's documentation: [docs.claude.com](https://docs.claude.com/) for
  Claude Code commands, hooks reference, and agent/skill syntax.
