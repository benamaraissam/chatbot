# Testing

This monorepo has 71 test files across the three libraries. Every PR runs
the full matrix in CI. Coverage is produced via the unified
[`coverage/run-coverage.sh`](../../coverage/run-coverage.sh) script.

## Test runners — at a glance

| Library | Runner | Coverage tool | Spec file pattern | Count |
|---|---|---|---|---|
| Python | `pytest` (asyncio auto-mode) | `pytest-cov` + `coverage[toml]` | `tests/test_*.py` | 27 |
| React | `vitest` (jsdom) | `@vitest/coverage-v8` | `src/**/*.test.{ts,tsx}` | 17 |
| Angular | `karma` + `jasmine` (Chrome Headless) | `karma-coverage` | `**/*.spec.ts` | 27 |

## Run everything

```bash
make -C coverage coverage          # all three, with coverage and a consolidated report
make -C coverage coverage-python   # only Python
make -C coverage coverage-react    # only React
make -C coverage coverage-angular  # only Angular
make -C coverage open              # open coverage/report.html in your browser
make -C coverage clean             # remove all coverage outputs
```

The script writes:

- `coverage/report.html` — consolidated dashboard (this is the main one)
- `coverage/report.md` — markdown version of the same table
- `coverage/_logs/{python,react,angular}.log` — per-library captured output
- `chatbot-python-library/coverage/` — per-file Istanbul-style report
- `chatbot-react-library/coverage/` — same
- `chatbot-angular-library/coverage/chatbot-angular/` — same

## Run a single library directly

When you're iterating, skip the orchestrator:

```bash
# Python
cd chatbot-python-library
pytest tests/test_chatbot.py -v
pytest tests/test_tools.py::test_register_python_callable -v
pytest -x --showlocals             # stop on first failure
pytest --cov=chatbot --cov-report=term-missing

# React
cd chatbot-react-library
npm test                           # watch mode
npm run test:run                   # one-shot
npm run test:coverage              # with v8 coverage
npx vitest run src/utils/id.test.ts

# Angular
cd chatbot-angular-library
npm test                                                                            # watch mode
npm test -- --watch=false --browsers=ChromeHeadless                                 # one-shot
npm test -- --code-coverage --watch=false --browsers=ChromeHeadless                 # with coverage
npx ng test chatbot-angular --include "**/primaryColor.spec.ts" --watch=false       # one spec
```

## File placement

### Python

Tests mirror the package layout: `src/chatbot/<area>` → `tests/test_<area>.py`.
A single file may aggregate several closely-related modules. The full
mapping is in
[`chatbot-python-library/.claude/skills/write-tests/SKILL.md`](../../chatbot-python-library/.claude/skills/write-tests/SKILL.md).

### React

Tests live **next to the source** as `<name>.test.ts` (or `.test.tsx` for
components):

```
src/utils/id.ts             ⇄ src/utils/id.test.ts
src/components/CopyButton.tsx ⇄ src/components/CopyButton.test.tsx
src/core/store.ts           ⇄ src/core/store.test.ts + src/core/store.advanced.test.ts
```

### Angular

Same convention — `<name>.spec.ts` next to the source under
`projects/chatbot-angular/src/lib/`.

## Canonical patterns

### Python — async test against the agent loop

```python
async def test_single_turn():
    from chatbot.core.chatbot import Chatbot
    from chatbot.providers.mock import MockProvider

    bot = Chatbot(provider=MockProvider.reply("hello"))
    reply = await bot.send("hi")
    assert reply.text == "hello"
```

### Python — FastAPI integration test

```python
async def test_chat_endpoint(agent_fixture):
    import httpx
    from fastapi import FastAPI
    from chatbot.integrations.fastapi import mount

    app = FastAPI()
    mount(app, agent=agent_fixture)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream("POST", "/chat", json={...}) as response:
            chunks = [c async for c in response.aiter_text()]
            assert any('"type": "message_end"' in c for c in chunks)
```

Never spin up uvicorn from a test.

### React — Vitest + Testing Library

```tsx
import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CopyButton } from "./CopyButton";

describe("<CopyButton />", () => {
  it("flips to Copied state after click", () => {
    render(<CopyButton text="hi" />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("button", { name: /copied/i })).toBeInTheDocument();
  });
});
```

The jsdom environment is configured in
[`vitest.config.ts`](../../chatbot-react-library/vitest.config.ts) and
[`src/test/setup.ts`](../../chatbot-react-library/src/test/setup.ts).
The setup file polyfills `window.matchMedia`, `URL.createObjectURL`,
`URL.revokeObjectURL`, and `Element.prototype.scrollIntoView` — APIs jsdom
does not implement.

### React — full composition test with mocked SSE

```tsx
function mockSSE(): Response {
  const enc = new TextEncoder();
  return new Response(new ReadableStream({
    start(c) {
      c.enqueue(enc.encode('event: text_delta\ndata: {"delta":"hi"}\n\n'));
      c.enqueue(enc.encode('event: done\ndata: {}\n\n'));
      c.close();
    },
  }), { status: 200 });
}

globalThis.fetch = vi.fn().mockResolvedValue(mockSSE()) as unknown as typeof fetch;

render(
  <ChatbotProvider endpoint="/api/chat" persist={false}>
    <FloatingChatbot />
  </ChatbotProvider>,
);

fireEvent.click(screen.getByRole("button", { name: /open chat/i }));
// ...
```

### Angular — TestBed component spec

```ts
import { TestBed } from "@angular/core/testing";
import { CopyButtonComponent } from "./copy-button.component";

describe("CopyButtonComponent", () => {
  let fixture: ComponentFixture<CopyButtonComponent>;
  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [CopyButtonComponent] }).compileComponents();
    fixture = TestBed.createComponent(CopyButtonComponent);
    fixture.detectChanges();
  });

  it("renders the Copy label", () => {
    expect(fixture.nativeElement.textContent).toContain("Copy");
  });
});
```

### Angular — service test with mocked fetch

```ts
const svc: ChatbotService = TestBed.inject(ChatbotService);
globalThis.fetch = jasmine.createSpy("fetch").and.resolveTo(
  new Response(readable([
    'event: message_start\ndata: {"id":"m_a","role":"assistant"}\n\n',
    'event: text_delta\ndata: {"delta":"hi"}\n\n',
    'event: message_end\ndata: {}\n\n',
    'event: done\ndata: {}\n\n',
  ]), { status: 200 }),
);
await svc.sendMessage("hi");
expect(svc.messages().length).toBe(2);
```

## Conventions

- **Mock at the boundary** — `MockProvider` / `scripted_provider` for LLMs,
  `httpx_mock` or `respx` for HTTP (Python), `globalThis.fetch` for SSE
  (TS), `Object.defineProperty(navigator, "clipboard", …)` for clipboard
  APIs.
- **Tests run hermetically** — no network calls, no real clipboard, no
  shared state. A test must work in isolation when run with `pytest -x` or
  `vitest run -t "<name>"`.
- **No `xit` / `xdescribe` / `pytest.skip`** unless gated on a missing
  optional service (Postgres, Redis) via env-var check.
- **Reproduce-then-fix for bugs** — write the failing test first; confirm
  it fails on the unpatched code; apply the fix; re-run.

## Adding a new test (cheat sheet)

The `.claude/skills/write-tests/SKILL.md` file in each library describes the
exact patterns Claude follows. The same patterns apply to humans:

1. Find the matching test module (or create `tests/test_<area>.py` /
   `<name>.test.ts` / `<name>.spec.ts`).
2. Mock at the right boundary — never call the network.
3. Write one assertion per concept; multiple `it` blocks if you cover
   different states.
4. Run only the new test, then the full file, then the suite.

## Coverage targets

Current statement coverage (see `coverage/report.html` after the latest run
for the live number):

- Python: ~80%
- React: ~80%
- Angular: ~80%

These are realistic, not aspirational — files that genuinely cannot be unit-tested
without external services (Postgres, web-search APIs, Django Channels, the
sandboxed code interpreter) are explicitly excluded via the coverage `omit`
list in
[`chatbot-python-library/pyproject.toml`](../../chatbot-python-library/pyproject.toml).

## See also

- [CI / CD](ci-cd.md) — how these tests run on every PR
- [Claude in development](claude.md) — how Claude helps write new tests
