# Angular library — `chatbot-angular`

An Angular 17 standalone-components library with a signal-driven service.
Functionally identical to the React library — same wire protocol, same
design tokens. Ships on npm as `chatbot-angular`.

> Source: [`chatbot-angular-library/`](../../chatbot-angular-library/) ·
> Library README: [`chatbot-angular-library/README.md`](../../chatbot-angular-library/README.md) ·
> Claude Code context: [`CLAUDE.md`](../../chatbot-angular-library/CLAUDE.md)

## Install

```bash
npm install chatbot-angular
```

Peer dependencies:

- `@angular/common` ≥ 17.3.0
- `@angular/core` ≥ 17.3.0

## Quickstart

Provide the config via the `CHATBOT_CONFIG` injection token in your
`ApplicationConfig`:

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

Drop the component into your template:

```html
<!-- app.component.html -->
<cb-floating-chatbot />
```

The selector prefix `cb-` is set by the library — you do not need to import
any module. All components are standalone, so import the specific component
where you use it:

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

## Public API surface

```ts
// DI
CHATBOT_CONFIG, ChatbotConfig, DEFAULT_STORAGE_KEY_ANGULAR

// Service
ChatbotService

// Types — mirror of the wire protocol
PROTOCOL_VERSION, PROTOCOL_HEADER, ChatRequest, Message, MessagePart,
TextPart, ImagePart, FilePart, ToolCallState, ParsedSSEEvent, SSEEventType

// Transport
streamChat, ChatbotStreamError

// Utils (commonly needed by consumers)
createId, resolveTheme, ThemeMode, ResolvedTheme,
buildPrimaryColorStyle, parseColor,
formatFileSize, getMessageText, isFilePart, isImageLikePart,
getToolsForMessage, formatToolName, getToolInputSummary, formatToolInput,
PendingAttachment, DEFAULT_ATTACHMENT_ACCEPT, validateAttachmentBatch,
filesToAttachmentParts, pendingAttachmentsToParts, detachPendingAttachments,
withImageDefaultText, registerDisplayUrl

// Components (selectors all start with `cb-`)
FloatingChatbotComponent, FloatingButtonComponent, ChatWindowComponent,
ChatHeaderComponent, ChatInputComponent, MessageListComponent,
MessageBubbleComponent, AssistantTurnComponent, PendingAssistantTurnComponent,
ThinkingIndicatorComponent, StreamingCursorComponent,
StreamingAnswerIndicatorComponent, MarkdownMessageComponent,
CopyButtonComponent, BotAvatarComponent, ToolCallCardComponent,
MessageAttachmentsComponent, ComposerAttachmentsComponent
```

## Config

The `ChatbotConfig` shape mirrors the React provider props:

```ts
interface ChatbotConfig {
  endpoint: string;
  headers?: Record<string, string>;
  getHeaders?: () => Record<string, string> | Promise<Record<string, string>>;
  model?: string;
  metadata?: Record<string, unknown>;
  storageKey?: string;
  persist?: boolean;
  title?: string;
  placeholder?: string;
  theme?: "light" | "dark" | "system";
  primaryColor?: string;
  allowThemeToggle?: boolean;
  onToolApproval?: (toolId: string, approved: boolean) => void | Promise<void>;
  suggestions?: string[];
  hostLayout?: "overlay" | "block";
  attachments?: {
    enabled?: boolean;
    maxCount?: number;
    maxSizeBytes?: number;
    accept?: string;
  };
}
```

## Reading state from your own components

`ChatbotService` exposes everything as Angular signals. Inject it and call
the signals like functions:

```ts
import { Component, computed, inject } from "@angular/core";
import { ChatbotService } from "chatbot-angular";

@Component({ /* ... */ })
export class HeaderComponent {
  private chatbot = inject(ChatbotService);

  isOpen = this.chatbot.isOpen;                       // Signal<boolean>
  messageCount = computed(() => this.chatbot.messages().length);

  toggle() { this.chatbot.toggleOpen(); }
}
```

Public service members:

```ts
// State signals (read-only)
isOpen, messages, conversationId,
isStreaming, isAwaitingReply,
streamingMessageId, streamingText, streamingThinkingText,
toolCalls, error,
theme, resolvedTheme,
panelWide, embeddedPanelCollapsed,
composerAttachments

// Methods
setOpen(open), toggleOpen()
togglePanelWide(), setEmbeddedPanelCollapsed(v), toggleEmbeddedPanelCollapsed()
setTheme(theme), setPrimaryColor(color)
setAttachmentsEnabled(enabled)
clearMessages()
addComposerAttachments(items), removeComposerAttachment(id), clearComposerAttachments()
addPendingFilePart(part), clearPendingFileParts()
upsertToolCall(id, patch)
stopStreaming()
async respondToToolApproval(toolId, approved)
async sendMessage(text, options?)
```

## Embedded layout (no FAB)

```html
<cb-chat-window embedded="true" />
```

This renders an always-visible panel that participates in your page layout
(no `position: fixed`). Combine with `hostLayout: "block"` in the config so
the root wrapper does not claim the viewport.

## Theming

Identical to the React library — three layers:

1. `primaryColor` config → sets `--cb-primary` + computed variants
2. Override any `--cb-*` CSS variable in your own stylesheet
3. The `data-cb-theme="light|dark"` attribute on the root drives the
   light/dark token set

The Angular library imports a single CSS file at build time:
`projects/chatbot-angular/src/lib/styles/chatbot-angular.css`. Make sure
your `angular.json` includes it (the demo app config has the line you need
to copy).

## SSE transport details

The transport is a `fetch` + `ReadableStream` consumer (matching the React
one) — see
[`src/lib/transport/sse-client.ts`](../../chatbot-angular-library/projects/chatbot-angular/src/lib/transport/sse-client.ts).

It is **not** Angular's `HttpClient` — `HttpClient` does not stream POST
response bodies. This means you do not need `HttpClientModule` in your
testing modules, and `HttpTestingController` will not work for these requests.
Stub `globalThis.fetch` in tests instead.

## Build outputs

`npm run build` (via `ng-packagr`) emits to `projects/chatbot-angular/dist/`:

- `fesm2022/chatbot-angular.mjs`
- `esm2022/...`
- `index.d.ts`
- `package.json` (with the right `exports`)

That `dist/` directory is what gets published to npm. Do **not** publish from
the workspace root.

## Testing

20 Karma + Jasmine spec files cover utils, the service (including the full
`sendMessage` SSE flow), the SSE transport, and most components. Headless
Chrome is the default runner.

```bash
npm test                                                       # watch mode
npm test -- --watch=false --browsers=ChromeHeadless            # one-shot
npm test -- --code-coverage --watch=false --browsers=ChromeHeadless
```

See [development/testing.md](../development/testing.md).

## Publishing

Tag `angular-v0.X.Y` and push — the GitHub Actions workflow rebuilds, runs
tests, and publishes the `dist/` artifact with provenance. See
[development/ci-cd.md](../development/ci-cd.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ɵcmp is not defined` at runtime | Library wasn't compiled with `ng-packagr` — run `npm run build` |
| Styles missing | Make sure `chatbot-angular.css` is in `angular.json` → `styles` |
| `HttpTestingController` does nothing | This library uses native `fetch`; stub `globalThis.fetch` instead |
| `ng test` says "test.ts missing from compilation" | The library tsconfig.spec.json must list `src/test.ts` under `files` |

## See also

- [Wire protocol](../wire-protocol.md) — the contract this library speaks
- [React library](react.md) — the sibling library with the same surface
