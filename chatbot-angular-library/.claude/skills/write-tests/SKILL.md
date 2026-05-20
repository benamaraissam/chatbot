---
name: write-tests
description: Use when adding a new test (or filling in coverage) for the chatbot-angular library. Triggers include "write a test for", "add a jasmine spec", "regression test", "test that this service/component...", or any request implying creation of a new spec in this repo.
---

# Writing tests for chatbot-angular

Tests use **Karma + Jasmine** with Angular's `TestBed`. Configuration:

- `karma.conf.js` at the workspace root
- `projects/chatbot-angular/tsconfig.spec.json`
- `projects/chatbot-angular/src/test.ts` bootstrap
- `architect.test` block in `angular.json`

## File placement

Tests live next to the source as `*.spec.ts`.

| Code under test | Spec file |
|---|---|
| `src/lib/utils/<name>.ts` | `src/lib/utils/<name>.spec.ts` |
| `src/lib/transport/sse-client.ts` | `src/lib/transport/sse-client.spec.ts` |
| `src/lib/services/chatbot.service.ts` | `src/lib/services/chatbot.service.spec.ts` |
| `src/lib/components/<name>/<name>.component.ts` | `src/lib/components/<name>/<name>.component.spec.ts` |

## Canonical patterns

### 1. Pure utility

```ts
import { parseColor } from './primaryColor';

describe('parseColor', () => {
  it('parses a 6-digit hex', () => {
    expect(parseColor('#0D9488')).toEqual({ r: 13, g: 148, b: 136 });
  });
});
```

### 2. Service with signal state (use TestBed)

```ts
import { TestBed } from '@angular/core/testing';
import { CHATBOT_CONFIG, ChatbotConfig } from '../tokens/chatbot-config.token';
import { ChatbotService } from './chatbot.service';

function setup(config: Partial<ChatbotConfig> = {}) {
  TestBed.configureTestingModule({
    providers: [
      { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat', ...config } },
      ChatbotService,
    ],
  });
  return TestBed.inject(ChatbotService);
}

describe('ChatbotService', () => {
  it('starts closed with no messages', () => {
    const svc = setup();
    expect(svc.isOpen()).toBeFalse();
    expect(svc.messages()).toEqual([]);
  });
});
```

### 3. SSE client (stub `fetch`)

```ts
import { streamChat, ChatbotStreamError } from './sse-client';

function readable(chunks: string[]) {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(c) { for (const x of chunks) c.enqueue(enc.encode(x)); c.close(); },
  });
}

describe('streamChat', () => {
  let original: typeof fetch;
  beforeEach(() => { original = globalThis.fetch; });
  afterEach(() => { globalThis.fetch = original; });

  it('throws on non-2xx', async () => {
    globalThis.fetch = jasmine.createSpy('fetch').and.resolveTo(
      new Response(null, { status: 502 }),
    );
    let err: unknown = null;
    try {
      await streamChat({
        endpoint: '/api/chat',
        body: { conversationId: 'c', messages: [] } as never,
        onEvent: () => {},
      });
    } catch (e) { err = e; }
    expect(err).toBeInstanceOf(ChatbotStreamError);
  });
});
```

### 4. Standalone component

```ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BotAvatarComponent } from './bot-avatar.component';

describe('BotAvatarComponent', () => {
  let fixture: ComponentFixture<BotAvatarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BotAvatarComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(BotAvatarComponent);
    fixture.detectChanges();
  });

  it('renders the avatar wrapper', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-bot-avatar-wrap')).not.toBeNull();
  });

  it('reacts to the loading input', () => {
    fixture.componentRef.setInput('loading', true);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-bot-loading')).not.toBeNull();
  });
});
```

## Conventions

- **Standalone components.** All components in this library are standalone;
  import the component directly in `TestBed.configureTestingModule({ imports: [...] })`.
- **Signal-driven state.** Services and components use `signal()` extensively.
  Read signals by calling them as functions in assertions:
  `expect(svc.isOpen()).toBeFalse()`.
- **Inputs.** Use `fixture.componentRef.setInput('name', value)` for the
  Angular 16+ signal-input API used in this library.
- **TestBed.inject** to fetch services — do not `new` them directly because
  they depend on injected tokens (`CHATBOT_CONFIG`).
- **Module imports.** For services with HTTP, do not use `HttpClientModule`
  in tests — this library uses native `fetch`, so stub `globalThis.fetch`
  instead.

## Running what you wrote

```bash
# All specs (watch mode in a desktop browser)
npm test

# CI mode — headless, single run
npm test -- --watch=false --browsers=ChromeHeadless

# A single spec file via ng test's --include flag
npx ng test chatbot-angular --include "**/primaryColor.spec.ts" --watch=false --browsers=ChromeHeadless
```

## Common mistakes to avoid

- Using `HttpTestingController` — this library uses `fetch`, not Angular's
  `HttpClient`. Stub `globalThis.fetch` instead.
- Forgetting `fixture.detectChanges()` after `setInput`.
- Importing a component into both `declarations` and `imports`. Standalone
  components only go into `imports`.
- Creating tests that depend on real network or `setTimeout` ticking the
  CD loop — wrap async logic with `fakeAsync` + `tick()` when needed.
