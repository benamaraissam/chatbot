# chatbot-react

Embeddable React chatbot with SSE streaming, multimodal attachments, tool
cards, and a thinking-trace UI. Drop it into any React 17/18 app in a few
lines.

> Full documentation: [docs/libraries/react.md](../docs/libraries/react.md)

## Install

```bash
npm install chatbot-react
```

Peer dependencies (your app must already have):

- `react` ≥ 17
- `react-dom` ≥ 17

Optional peer: `shiki` for syntax-highlighted code blocks (falls back to
plain code blocks when absent).

## Quickstart

```tsx
import { ChatbotProvider, FloatingChatbot } from "chatbot-react";
import "chatbot-react/styles.css";

export function App() {
  return (
    <ChatbotProvider
      endpoint="/api/chat"
      title="Assistant"
      theme="system"
      persist={true}
    >
      {/* your app */}
      <FloatingChatbot />
    </ChatbotProvider>
  );
}
```

That's the entire integration. `endpoint` points at your Python backend's
mount point (default `/api/chat`).

## Provider configuration (selected)

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
  suggestions?: string[];                    // shown in empty state
  attachments?: {
    enabled?: boolean;                       // default: true
    maxCount?: number;                       // default: 5
    maxSizeBytes?: number;                   // default: 5 MB
    accept?: string;
  };
  hostLayout?: "overlay" | "block";          // default: "overlay"
  onToolApproval?: (toolId: string, approved: boolean) => void | Promise<void>;
}
```

Full options + theming, hooks, and embedded sidebar mode are documented in
[docs/libraries/react.md](../docs/libraries/react.md).

## Public exports

- **Provider** — `ChatbotProvider`, `useChatbotContext`
- **Hooks** — `useChatbot`, `useChatbotActions`, `useConversation`, `useStreamingChat`
- **Components** — `FloatingChatbot`, `FloatingButton`, `ChatWindow`, `ChatHeader`,
  `ChatInput`, `MessageList`, `MessageBubble`, `AssistantTurn`,
  `ThinkingIndicator`, `StreamingCursor`, `MarkdownMessage`, `CodeBlock`,
  `CopyButton`, `BotAvatar`, `ToolCallCard`, `AttachmentImage`,
  `MessageAttachments`, `ComposerAttachments`, …
- **Types** — `Message`, `MessagePart`, `ToolCallState`, `ChatRequest`,
  `ChatbotConfig`, `ThemeMode`, `ChatbotStreamError`

## Custom trigger / state access

```tsx
import { useChatbot, useChatbotActions } from "chatbot-react";

function CustomTrigger() {
  const isOpen = useChatbot((s) => s.isOpen);
  const { toggleOpen } = useChatbotActions();
  return <button onClick={toggleOpen}>{isOpen ? "Close" : "Open"} chat</button>;
}
```

## Demo

```bash
npm install
npm run dev   # http://localhost:5173
```

The demo expects a backend on `http://localhost:8000/chat` — see the Python
library README for how to start one.

## Build outputs

`npm run build` (Vite library mode) emits to `dist/`:

- `chatbot-react.js` (ESM)
- `chatbot-react.umd.cjs` (UMD)
- `chatbot-react.css`
- `index.d.ts`

## Tests

```bash
npm test                    # watch mode
npm run test:run            # one-shot
npm run test:coverage       # with v8 coverage
```

Or from the repo root:

```bash
make -C coverage coverage-react
```

See [`docs/development/testing.md`](../docs/development/testing.md).

## Publishing

Tag-driven via GitHub Actions — push a `react-v0.X.Y` tag and the workflow
runs typecheck + tests + build and publishes to npm with provenance. See
[`docs/development/ci-cd.md`](../docs/development/ci-cd.md).

## License

MIT.
