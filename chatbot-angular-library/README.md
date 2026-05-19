# chatbot-angular

Angular 17+ UI library for the chatbot Python backend. Streaming SSE, tool call cards, file downloads, thinking traces, and attachment support — all built with standalone components and Angular signals.

---

## Installation

```bash
npm install chatbot-angular
```

Peer dependencies: `@angular/core` and `@angular/common` ≥ 17.3.

---

## Quick start

### 1. Provide the config

In your `app.config.ts` (standalone bootstrap):

```typescript
import { ApplicationConfig } from '@angular/core';
import { CHATBOT_CONFIG } from 'chatbot-angular';

export const appConfig: ApplicationConfig = {
  providers: [
    {
      provide: CHATBOT_CONFIG,
      useValue: {
        endpoint: '/api/chat',  // your FastAPI / Flask / Django backend
        title: 'My Assistant',
        theme: 'system',
        allowThemeToggle: true,
      },
    },
  ],
};
```

Or at component level if you want per-component config:

```typescript
@Component({
  providers: [
    ChatbotService,
    { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat' } },
  ],
})
export class MyComponent {}
```

### 2. Import the CSS

In `styles.css` (or `angular.json` `styles` array):

```css
@import 'chatbot-angular/styles';
```

### 3. Drop in the floating chatbot

```typescript
import { FloatingChatbotComponent } from 'chatbot-angular';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [FloatingChatbotComponent],
  template: `<cb-floating-chatbot />`,
})
export class AppComponent {}
```

That's it. A floating button appears in the bottom-right corner; clicking it opens the chat overlay.

---

## ChatbotConfig options

| Option | Type | Default | Description |
|---|---|---|---|
| `endpoint` | `string` | — | **Required.** SSE chat endpoint URL. |
| `headers` | `Record<string, string>` | `{}` | Static extra headers sent with every request. |
| `getHeaders` | `() => Record<string,string> \| Promise<…>` | — | Async header factory (e.g. for auth tokens). |
| `model` | `string` | — | Model override passed to the backend. |
| `metadata` | `Record<string, unknown>` | `{}` | Extra metadata merged into every request body. |
| `storageKey` | `string` | `'chatbot-angular:conversation'` | `localStorage` key for conversation persistence. |
| `persist` | `boolean` | `false` | Persist conversation across page reloads. |
| `title` | `string` | `'Assistant'` | Header title. |
| `placeholder` | `string` | `'Message…'` | Textarea placeholder. |
| `theme` | `'light' \| 'dark' \| 'system'` | `'system'` | Initial theme. |
| `primaryColor` | `string` | — | CSS hex/hsl to override the primary accent. |
| `allowThemeToggle` | `boolean` | `true` when `theme='system'` | Show sun/moon toggle in header. |
| `suggestions` | `string[]` | (demo hints) | Quick-send chips shown on empty state. |
| `hostLayout` | `'overlay' \| 'block'` | `'overlay'` | Layout mode for the root container. |
| `attachments.enabled` | `boolean` | `true` | Enable file/image attachment picker. |
| `attachments.maxCount` | `number` | — | Max attachments per message. |
| `attachments.maxSizeBytes` | `number` | — | Max file size per attachment. |
| `attachments.accept` | `string` | `'image/*,…'` | `accept` attribute for the file input. |
| `onToolApproval` | `(id, approved) => void \| Promise<void>` | — | Called after the user approves/denies a tool. |

---

## Components

All components are standalone. Import only what you need.

### All-in-one

| Component | Selector | Description |
|---|---|---|
| `FloatingChatbotComponent` | `<cb-floating-chatbot>` | FAB button + overlay window. The easiest drop-in. |
| `ChatWindowComponent` | `<cb-chat-window>` | The chat panel. Use `[embedded]="true"` for sidebar mode. |

### Layout

| Component | Selector | Description |
|---|---|---|
| `ChatHeaderComponent` | `<cb-chat-header>` | Title, theme toggle, clear, and close buttons. |
| `MessageListComponent` | `<cb-message-list>` | Scrollable list of messages, empty state, and error display. |
| `ChatInputComponent` | `<cb-chat-input>` | Composer with attachment picker, textarea, and send/stop. |

### Messages

| Component | Selector | Description |
|---|---|---|
| `MessageBubbleComponent` | `<cb-message-bubble>` | Single user or assistant text bubble. |
| `AssistantTurnComponent` | `<cb-assistant-turn>` | Avatar + thinking trace + tool cards + bubble. |
| `PendingAssistantTurnComponent` | `<cb-pending-assistant-turn>` | Loading placeholder while waiting for a reply. |
| `MarkdownMessageComponent` | `<cb-markdown-message>` | Safe markdown renderer. |
| `ToolCallCardComponent` | `<cb-tool-call-card>` | Expandable tool call with parameters, result, and approval UI. |
| `MessageAttachmentsComponent` | `<cb-message-attachments>` | Image and file attachments on a message. |

### Primitives

| Component | Selector | Description |
|---|---|---|
| `FloatingButtonComponent` | `<cb-floating-button>` | The FAB button alone (without window). |
| `ComposerAttachmentsComponent` | `<cb-composer-attachments>` | Attachment chips in the composer. |
| `ThinkingIndicatorComponent` | `<cb-thinking-indicator>` | Collapsible reasoning trace. |
| `CopyButtonComponent` | `<cb-copy-button>` | Clipboard copy with 2 s feedback. |
| `BotAvatarComponent` | `<cb-bot-avatar>` | Bot icon with loading dots animation. |

---

## Embedded / sidebar mode

```typescript
import { ChatWindowComponent } from 'chatbot-angular';

@Component({
  standalone: true,
  imports: [ChatWindowComponent],
  template: `
    <div style="display:flex; height:100vh;">
      <main style="flex:1">…your app…</main>
      <cb-chat-window [embedded]="true" />
    </div>
  `,
})
export class AppComponent {}
```

Pass `[collapsible]="false"` to remove the collapse toggle from the sidebar.

---

## Accessing the service directly

`ChatbotService` exposes all state as read-only signals:

```typescript
import { ChatbotService } from 'chatbot-angular';

@Component({ … })
export class MyComponent {
  private chatbot = inject(ChatbotService);

  readonly messages = this.chatbot.messages;       // Signal<Message[]>
  readonly isStreaming = this.chatbot.isStreaming;  // Signal<boolean>

  send(text: string) {
    void this.chatbot.sendMessage(text);
  }
}
```

The service must be provided alongside `CHATBOT_CONFIG` — either via `app.config.ts` providers or directly on the component.

---

## Theming

The library uses CSS custom properties under `[data-cb-theme]`. Override any token:

```css
[data-cb-theme] {
  --cb-primary: #0066cc;
  --cb-radius: 0.75rem;
}
```

Or pass `primaryColor` to `CHATBOT_CONFIG` to override the accent programmatically.

---

## Demo app

A demo app is included under `projects/demo/`. To run it locally:

```bash
cd chatbot-angular-library

# Install dependencies
npm install

# Start the Python backend (from the repo root)
cd ../chatbot-python-library/examples/02_web_apps
python fastapi_app.py

# Start the Angular demo (in a second terminal)
cd chatbot-angular-library
npx ng serve demo --port 4200
```

Open [http://localhost:4200](http://localhost:4200). The demo shows three modes: **Floating** (overlay FAB), **Embedded** (collapsible sidebar), and **Block** (always-visible panel).

---

## Building the library

```bash
npx ng build chatbot-angular
```

The output lands in `dist/chatbot-angular/`. To publish:

```bash
cd dist/chatbot-angular
npm publish
```

---

## Differences from chatbot-react-library

| | React | Angular |
|---|---|---|
| State | Zustand store + Context | `ChatbotService` with Angular signals |
| Styling | Tailwind utility classes | Same `cb-*` CSS custom properties |
| Icons | lucide-react | Inline SVG |
| Animations | framer-motion | CSS transitions |
| Markdown | react-markdown | Built-in `markdownToHtml()` + `DomSanitizer` |
| Min version | React 18 | Angular 17.3 |
