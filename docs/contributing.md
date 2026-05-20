# Contributing

Thanks for considering a contribution. This is a small monorepo with three
sibling libraries — most contributions touch only one of them.

## Before you start

Open an issue or pull-request draft so we can sanity-check the direction.
For bug fixes, paste the failing case (test, log, or repro steps) — that
turns the conversation into a small, scoped change.

## Quickstart for contributors

```bash
git clone <repo>
cd ChatBot

# Per library — install once
cd chatbot-python-library  && uv sync --group dev      && cd ..
cd chatbot-react-library   && npm install              && cd ..
cd chatbot-angular-library && npm install              && cd ..

# Run all tests + coverage in one go
make -C coverage coverage
make -C coverage open                                  # opens coverage/report.html
```

## Branching and PRs

- `main` is the integration branch — always green in CI.
- Branch from `main`. Name the branch by topic (`fix/sqlite-cursor-leak`,
  `feat/litestar-adapter`).
- One concern per PR. If you find another bug while fixing the first,
  open a separate PR — it makes review much faster.
- Rebase rather than merge `main` into your branch.

## Code style

| Library | Linter / formatter | Command |
|---|---|---|
| Python | `ruff` (line length 100, rules E/F/I/UP) | `ruff format src/ tests/ && ruff check --fix src/ tests/` |
| React | TypeScript `strict` mode | `npm run typecheck` |
| Angular | TypeScript `strict` mode | `npx tsc -p projects/chatbot-angular/tsconfig.lib.json --noEmit` |

The Claude hooks run these automatically after edits — see
[development/claude.md](development/claude.md).

## Tests are required

Every behaviour change ships with a test. The exceptions are:

- Pure documentation or comment changes
- Refactors that the existing suite already covers

Look at the patterns in [development/testing.md](development/testing.md)
before adding new tests. If the area you're touching has no test file
yet, create one — the [`write-tests` skills](../chatbot-python-library/.claude/skills/write-tests/SKILL.md)
in each library describe placement conventions.

## Wire-protocol changes

The wire protocol is shared across all three libraries. If you change it:

1. Update [`docs/wire-protocol.md`](wire-protocol.md) first.
2. Update Python `protocol/schemas.py` + `protocol/sse.py`.
3. Update React `src/types/protocol.ts` + `src/transport/sseClient.ts`.
4. Update Angular `projects/chatbot-angular/src/lib/types/protocol.ts` +
   `src/lib/transport/sse-client.ts`.
5. Bump `PROTOCOL_VERSION` if it is a breaking change.
6. Add tests that exercise the new event/shape in each library.

Skipping any step leaves the codebase in an inconsistent state and will
break CI.

## Adding a new framework adapter

The Python library is framework-agnostic. To add a new adapter (e.g.
Litestar):

1. Read
   [`chatbot-python-library/.claude/skills/add-framework-adapter/SKILL.md`](../chatbot-python-library/.claude/skills/add-framework-adapter/SKILL.md).
2. Create `src/chatbot/integrations/<framework>.py` exposing `mount(app,
   *, agent, path="/chat", sse=True)`.
3. Add the optional dependency under `[project.optional-dependencies]` in
   `pyproject.toml`.
4. Add it to the `all` extra.
5. Add `tests/test_integration_<framework>.py` exercising single-turn and
   streaming with `httpx.AsyncClient`.

## Adding a new component

For React or Angular UI components, keep the contracts identical between
the two libraries:

- Same selector / component name minus the framework idiom
  (`<CopyButton />` ↔ `<cb-copy-button />`).
- Same input props / signal inputs.
- Same accessible structure — assertions in tests on `role` + `aria-label`
  pass identically in both libraries.

## Releasing

Tag-driven — see [development/ci-cd.md](development/ci-cd.md). Maintainers
do this; contributors don't need to.

## Code of conduct

Be excellent to each other. Disagreements are normal; personal attacks are
not. Reviewers: assume good faith and explain the *why* behind requests.

## Where to get help

- File an issue with the failing case
- Tag a maintainer if a PR has been waiting more than a week without
  feedback

## See also

- [Architecture](architecture.md)
- [Testing](development/testing.md)
- [CI / CD](development/ci-cd.md)
- [Claude in development](development/claude.md)
