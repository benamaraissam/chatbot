---
name: write-tests
description: Use when adding a new test (or filling in coverage) for the chatbot-react library. Triggers include "write a test for", "add a vitest test", "regression test", "test that this hook/component...", or any request implying creation of a new test in this repo.
---

# Writing tests for chatbot-react

Tests use **Vitest** with **jsdom** and `@testing-library/react`. The runner
config is in `vitest.config.ts`; `src/test/setup.ts` extends the matchers
with `@testing-library/jest-dom`.

## File placement

Tests live next to the source they cover, with a `.test.ts` (or `.test.tsx`
for components) suffix.

| Code under test | Test file |
|---|---|
| `src/utils/<name>.ts` | `src/utils/<name>.test.ts` |
| `src/core/store.ts` | `src/core/store.test.ts` |
| `src/core/ChatbotProvider.tsx` | `src/core/ChatbotProvider.test.tsx` |
| `src/transport/sseClient.ts` | `src/transport/sseClient.test.ts` |
| `src/hooks/<name>.ts` | `src/hooks/<name>.test.tsx` (uses `renderHook`) |
| `src/components/<Name>.tsx` | `src/components/<Name>.test.tsx` |

## Canonical patterns

### 1. Pure utility

```ts
import { describe, expect, it } from "vitest";
import { parseColor } from "./primaryColor";

describe("parseColor", () => {
  it("parses a 6-digit hex", () => {
    expect(parseColor("#0D9488")).toEqual({ r: 13, g: 148, b: 136 });
  });
});
```

### 2. Zustand store

```ts
import { describe, expect, it } from "vitest";
import { createChatbotStore } from "./store";

describe("chatbot store", () => {
  it("toggleOpen flips isOpen", () => {
    const useStore = createChatbotStore();
    useStore.getState().toggleOpen();
    expect(useStore.getState().isOpen).toBe(true);
  });
});
```

### 3. SSE client (mock `fetch`)

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { streamChat, ChatbotStreamError } from "./sseClient";

function readable(chunks: string[]) {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(c) { for (const x of chunks) c.enqueue(enc.encode(x)); c.close(); },
  });
}

describe("streamChat", () => {
  let original: typeof fetch;
  beforeEach(() => { original = globalThis.fetch; });
  afterEach(() => { globalThis.fetch = original; vi.restoreAllMocks(); });

  it("parses SSE frames", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(readable(["event: text_delta\ndata: {\"delta\":\"hi\"}\n\n"]),
        { status: 200 }),
    ) as unknown as typeof fetch;

    const events: string[] = [];
    await streamChat({
      endpoint: "/api/chat",
      body: { conversationId: "c", messages: [] } as never,
      onEvent: (e) => events.push(e.type),
    });
    expect(events).toContain("text_delta");
  });
});
```

### 4. React component

```tsx
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { CopyButton } from "./CopyButton";

describe("<CopyButton />", () => {
  it("renders an accessible button", () => {
    render(<CopyButton text="hello" />);
    expect(screen.getByRole("button", { name: /copy/i })).toBeInTheDocument();
  });
});
```

### 5. Hook (use `renderHook`)

```tsx
import { renderHook, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useChatbot } from "./useChatbot";

describe("useChatbot", () => {
  it("exposes the current open state", () => {
    const { result } = renderHook(() => useChatbot((s) => s.isOpen));
    expect(result.current).toBe(false);
  });
});
```

## Conventions

- Use **`describe` blocks** to group tests for one symbol; the description
  is the symbol name in backticks.
- For DOM tests, query by **accessible role/name first**, then by text, then
  by `data-testid` as a last resort.
- **Mock `fetch` at `globalThis.fetch`**, restore in `afterEach`. Never
  monkey-patch internal modules.
- Reset zustand stores by creating a new instance with `createChatbotStore()`
  per test — never share global state between tests.
- For tests touching `window.matchMedia`, stub via `vi.stubGlobal` and
  unstub in `afterEach`.

## Running what you wrote

```bash
# Watch mode (default `npm test`)
npm test

# One-shot CI mode
npm run test:run

# A single file
npx vitest run src/utils/primaryColor.test.ts

# A single test by name
npx vitest run -t "parses a 6-digit hex"
```

## Common mistakes to avoid

- Importing the source under test **before** stubbing `fetch`. Either stub
  in `beforeEach` and import statically (the function captures the binding
  at call time), or import dynamically inside the test after stubbing.
- Forgetting `cleanup()` — `@testing-library/react` auto-cleans between
  tests when `vitest` sees `vitest/config`, but check the config if you see
  state leak across tests.
- Asserting on internal CSS class names. Assert on accessible structure
  and visible text instead.
- Using `act()` inappropriately. With Testing Library you rarely need it —
  reach for `findByRole` / `waitFor` for async UI changes.
