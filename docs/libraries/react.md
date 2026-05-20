# React library — `chatbot-react`

An embeddable React chatbot with SSE streaming, multimodal attachments, tool
cards, and a thinking-trace UI. Ships on npm as `chatbot-react`.

> Source: [`chatbot-react-library/`](../../chatbot-react-library/) ·
> Library README: [`chatbot-react-library/README.md`](../../chatbot-react-library/README.md) ·
> Claude Code context: [`CLAUDE.md`](../../chatbot-react-library/CLAUDE.md) ·
> Design system reference: [`design-system/`](../../chatbot-react-library/design-system/)

## Install

```bash
npm install chatbot-react
```

Peer dependencies (your app must already have):

- `react` ≥ 17 (React 17 and 18 are both supported)
- `react-dom` ≥ 17

Optional dependencies:

- `shiki` — used for syntax-highlighted code blocks in assistant markdown.
  Falls back to plain code blocks when absent.

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

That's the entire integration. `<FloatingChatbot />` renders the FAB and the
panel; you can swap in `<ChatWindow embedded />` for an always-visible
sidebar layout.

## Public API surface

```ts
// Provider + config
ChatbotProvider, useChatbotContext

// State (read-only selectors)
useChatbot(selector)           // any slice of the store
useConversation()              // { messages, conversationId, toolCalls }
useStreamingChat()             // { isStreaming, streamingText, streamingMessageId, error }

// Actions
useChatbotActions()
  // → sendMessage, stopStreaming, setOpen, toggleOpen, clearMessages,
  //   setTheme, togglePanelWide, setEmbeddedPanelCollapsed,
  //   toggleEmbeddedPanelCollapsed

// Components
FloatingChatbot, FloatingButton, ChatWindow, ChatHeader, ChatInput,
MessageList, MessageBubble, AssistantTurn, PendingAssistantTurn,
ThinkingIndicator, StreamingCursor, StreamingAnswerIndicator,
MarkdownMessage, CodeBlock, CopyButton, BotAvatar, ToolCallCard,
AttachmentImage, MessageAttachments, ComposerAttachments
```

## Provider configuration

```ts
interface ChatbotConfig {
  endpoint: string;                                      // required
  headers?: Record<string, string>;
  getHeaders?: () => Record<string, string> | Promise<Record<string, string>>;
  model?: string;
  metadata?: Record<string, unknown>;
  storageKey?: string;                                   // localStorage key
  persist?: boolean;                                     // default: true
  title?: string;
  placeholder?: string;
  theme?: "light" | "dark" | "system";
  primaryColor?: string;                                 // hex or rgb()
  allowThemeToggle?: boolean;                            // default: theme === "system"
  onToolApproval?: (toolId: string, approved: boolean) => void | Promise<void>;
  suggestions?: string[];                                // shown in empty state
  hostLayout?: "overlay" | "block";                      // default: overlay
  attachments?: {
    enabled?: boolean;                                   // default: true
    maxCount?: number;                                   // default: 5
    maxSizeBytes?: number;                               // default: 5 MB
    accept?: string;                                     // input[accept]
  };
}
```

Examples:

```tsx
// Add auth headers per request
<ChatbotProvider
  endpoint="/api/chat"
  getHeaders={async () => ({ Authorization: `Bearer ${await getToken()}` })}
>

// Brand color
<ChatbotProvider endpoint="/api/chat" primaryColor="#7c3aed" />

// Embedded sidebar layout (no FAB)
<ChatbotProvider endpoint="/api/chat" hostLayout="block">
  <ChatWindow embedded />
</ChatbotProvider>
```

## Component composition

`<FloatingChatbot />` is just `<><FloatingButton /><ChatWindow /></>`. Use
the lower-level components if you want a custom layout:

```tsx
<ChatbotProvider endpoint="/api/chat" hostLayout="block">
  <div className="my-sidebar">
    <ChatHeader />
    <MessageList />
    <ChatInput />
  </div>
</ChatbotProvider>
```

## Theming

Three layers, in priority order:

1. **`primaryColor`** prop on `ChatbotProvider` — sets `--cb-primary` and
   computes hover/glow/mute variants automatically.
2. **CSS variables** — you can override any `--cb-*` variable in your own
   stylesheet to retheme deeply (surfaces, text, borders, etc.). See the
   design system reference for the full token list.
3. **Tailwind utility classes** — all internal classes are prefixed with
   `cb-` so they don't collide with your app's Tailwind setup.

Light/dark/system mode is controlled by the `theme` prop and reflected via
the `data-cb-theme` attribute on the root wrapper.

## Hooks usage examples

```tsx
import { useChatbot, useChatbotActions, useConversation } from "chatbot-react";

function CustomTrigger() {
  const isOpen = useChatbot((s) => s.isOpen);
  const { toggleOpen } = useChatbotActions();
  return <button onClick={toggleOpen}>{isOpen ? "Close" : "Open"} chat</button>;
}

function MessageCount() {
  const { messages } = useConversation();
  return <span>{messages.length} message{messages.length === 1 ? "" : "s"}</span>;
}
```

## Programmatic sending

```tsx
const { sendMessage } = useChatbotActions();
await sendMessage("Summarize page", {
  approvedToolIds: ["t_pending"], // resume an approval-gated tool
  attachmentParts: [],
});
```

## SSE transport details

The transport is a `fetch` + `ReadableStream` consumer
([`src/transport/sseClient.ts`](../../chatbot-react-library/src/transport/sseClient.ts)),
not `EventSource` — because the request body is JSON-over-POST. The
following protocol headers are added automatically:

```
Content-Type:                application/json
Accept:                      text/event-stream
X-Chatbot-Protocol-Version:  1
```

Aborted streams release resources via `AbortController`. React strict mode's
double-mount does not leak streams in this implementation.

## Build outputs

`npm run build` (via Vite library mode) emits to `dist/`:

- `chatbot-react.js` — ESM
- `chatbot-react.umd.cjs` — UMD
- `chatbot-react.css` — compiled Tailwind + design tokens
- `index.d.ts` — type declarations

`package.json` `exports` map points at these paths, so consumers get the
right entry automatically.

## Testing

10 Vitest test files cover utils, store, transport, components, hooks, and
the full `<FloatingChatbot />` composition flow with a mocked SSE backend.

```bash
npm test                       # watch mode
npm run test:run               # one-shot
npm run test:coverage          # with v8 coverage + json + html reports
```

See [development/testing.md](../development/testing.md).

## Publishing

Tag `react-v0.X.Y` and push — the GitHub Actions workflow rebuilds, runs
tests, and publishes to npm with provenance. See
[development/ci-cd.md](../development/ci-cd.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| Code blocks render plain when they should be highlighted | `npm install shiki` in the host app — it's an optional peer |
| Streaming hangs behind a CDN | Disable proxy buffering (e.g. `X-Accel-Buffering: no` for nginx) |
| Multiple Tailwinds collide | All internal classes are `cb-*` prefixed; check your `tailwind.config.js` `content` globs do not include `node_modules/chatbot-react/**` |

## See also

- [Wire protocol](../wire-protocol.md) — exact SSE event flow
- [Angular library](angular.md) — the sibling library that speaks the same wire protocol
