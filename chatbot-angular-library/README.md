# chatbot-angular

Embeddable Angular 17 chatbot with SSE streaming, multimodal attachments,
tool cards, and a thinking-trace UI. Standalone components and signal-based
state — no NgModules required.

> Full documentation: [docs/libraries/angular.md](../docs/libraries/angular.md)

## Install

```bash
npm install chatbot-angular
```

Peer dependencies (your app must already have):

- `@angular/common` ≥ 17.3.0
- `@angular/core` ≥ 17.3.0

## Quickstart

### 1. Provide the config

```ts
// app.config.ts
import { ApplicationConfig } from "@angular/core";
import { CHATBOT_CONFIG } from "chatbot-angular";

export const appConfig: ApplicationConfig = {
  providers: [
    {
      provide: CHATBOT_CONFIG,
      useValue: {
        endpoint: "/api/chat",
        title: "Assistant",
        theme: "system",
        persist: true,
      },
    },
  ],
};
```

### 2. Import the CSS

Add the library stylesheet to your `angular.json`:

```json
"styles": [
  "src/styles.css",
  "node_modules/chatbot-angular/styles/chatbot-angular.css"
]
```

### 3. Drop in the component

```ts
import { Component } from "@angular/core";
import { FloatingChatbotComponent } from "chatbot-angular";

@Component({
  standalone: true,
  imports: [FloatingChatbotComponent],
  template: `<cb-floating-chatbot />`,
})
export class AppComponent {}
```

`endpoint` points at your Python backend's mount point (default `/api/chat`).

## Configuration

```ts
interface ChatbotConfig {
  endpoint: string;                          // required
  title?: string;
  placeholder?: string;
  theme?: "light" | "dark" | "system";       // default: "system"
  primaryColor?: string;                     // hex or rgb()
  persist?: boolean;                         // default: true
  storageKey?: string;                       // localStorage key
  headers?: Record<string, string>;
  getHeaders?: () => Record<string, string> | Promise<Record<string, string>>;
  suggestions?: string[];
  attachments?: {
    enabled?: boolean;
    maxCount?: number;
    maxSizeBytes?: number;
    accept?: string;
  };
  hostLayout?: "overlay" | "block";          // default: "overlay"
  onToolApproval?: (toolId: string, approved: boolean) => void | Promise<void>;
}
```

Full options, theming, and embedded sidebar mode are documented in
[docs/libraries/angular.md](../docs/libraries/angular.md).

## Public exports

- **DI** — `CHATBOT_CONFIG`, `ChatbotConfig`, `DEFAULT_STORAGE_KEY_ANGULAR`
- **Service** — `ChatbotService` (signal-based state + `sendMessage`)
- **Components** (all `cb-` prefixed) — `FloatingChatbotComponent`,
  `FloatingButtonComponent`, `ChatWindowComponent`, `ChatHeaderComponent`,
  `ChatInputComponent`, `MessageListComponent`, `MessageBubbleComponent`,
  `AssistantTurnComponent`, `ThinkingIndicatorComponent`,
  `StreamingCursorComponent`, `MarkdownMessageComponent`,
  `CopyButtonComponent`, `BotAvatarComponent`, `ToolCallCardComponent`,
  `MessageAttachmentsComponent`, `ComposerAttachmentsComponent`, …
- **Types** — `Message`, `MessagePart`, `ToolCallState`, `ChatRequest`,
  `ParsedSSEEvent`, `SSEEventType`, `ChatbotStreamError`

## State access from your own component

`ChatbotService` exposes everything as signals — inject it and call the
signals as functions:

```ts
import { Component, computed, inject } from "@angular/core";
import { ChatbotService } from "chatbot-angular";

@Component({ /* ... */ })
export class HeaderComponent {
  private chatbot = inject(ChatbotService);
  isOpen = this.chatbot.isOpen;
  count = computed(() => this.chatbot.messages().length);
  toggle() { this.chatbot.toggleOpen(); }
}
```

## Embedded layout (no FAB)

```html
<cb-chat-window embedded="true" />
```

Combine with `hostLayout: "block"` so the root wrapper does not claim the
viewport.

## Demo

```bash
npm install
npm run demo   # http://localhost:4200
```

The demo expects a backend on `http://localhost:8000/chat` — see the Python
library README for how to start one.

## Build

```bash
npm run build   # ng-packagr → dist/chatbot-angular/
```

The published artifact lives under `projects/chatbot-angular/dist/`.

## Tests

```bash
npm test                                                        # watch
npm test -- --watch=false --browsers=ChromeHeadless             # one-shot
npm test -- --code-coverage --watch=false --browsers=ChromeHeadless
```

Or from the repo root:

```bash
make -C coverage coverage-angular
```

See [`docs/development/testing.md`](../docs/development/testing.md).

## Publishing

Tag-driven via GitHub Actions — push an `angular-v0.X.Y` tag and the
workflow runs Karma + ng build and publishes the `dist/` artifact to npm
with provenance. See [`docs/development/ci-cd.md`](../docs/development/ci-cd.md).

## License

MIT.
