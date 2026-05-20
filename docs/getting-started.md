# Getting started

Run the full stack — Python backend + a React or Angular frontend — in about
five minutes.

## Prerequisites

- Python 3.11+
- Node.js 20 (Node 18 also works; Node 22+ may show warnings against the
  Angular 17 toolchain but generally works)
- An API key for at least one LLM provider (Anthropic, OpenAI, or Azure
  OpenAI). For local development you can skip this and use the `mock`
  provider that ships with the library.

## 1 — Backend

```bash
cd chatbot-python-library
python -m venv .venv && source .venv/bin/activate
pip install -e ".[fastapi]"

# Quick sanity check
pytest -q
```

Set an API key (any one is enough):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# OR
export OPENAI_API_KEY=sk-...
```

Start the bundled server:

```bash
chatbot serve --config config.yaml.example --port 8000
```

The server now exposes `POST /chat` at `http://localhost:8000/chat` (see
[wire-protocol.md](wire-protocol.md) for the exact contract).

Smoke-test it with curl:

```bash
curl -N -H 'Content-Type: application/json' \
  -d '{"messages":[{"id":"m1","role":"user","parts":[{"type":"text","text":"hi"}]}]}' \
  http://localhost:8000/chat
```

You should see an SSE stream of `message_start` → `text_delta` → `message_end`
→ `done`.

## 2 — Frontend (pick one)

### React

```bash
cd chatbot-react-library
npm install
npm run dev          # demo at http://localhost:5173
```

The demo automatically points at `http://localhost:8000/chat`. Open the
chatbot, type a message, watch the streaming response.

### Angular

```bash
cd chatbot-angular-library
npm install
npm run demo         # demo at http://localhost:4200
```

The Angular demo speaks to the same backend on `localhost:8000`. The two
demos are interchangeable — try opening both and you'll see the same UI,
just rendered through different frameworks.

## 3 — Library mode (skip the standalone server)

If you already have a FastAPI app, drop the chatbot into it directly:

```python
from fastapi import FastAPI
from chatbot import Chatbot
from chatbot.integrations.fastapi import mount

app = FastAPI()
bot = Chatbot(provider="anthropic", model="claude-3-5-sonnet")
mount(app, agent=bot, path="/api/chat")
```

That's the entire integration. The React or Angular library can be pointed
at `/api/chat` and everything just works.

The same pattern exists for Flask, Django, Starlette, and any ASGI app —
see [libraries/python.md](libraries/python.md).

## 4 — Embed the React widget in your own app

```bash
npm install chatbot-react
```

```tsx
import { ChatbotProvider, FloatingChatbot } from "chatbot-react";
import "chatbot-react/styles.css";

export function App() {
  return (
    <ChatbotProvider endpoint="/api/chat" title="Assistant">
      {/* your app */}
      <FloatingChatbot />
    </ChatbotProvider>
  );
}
```

Detail: [libraries/react.md](libraries/react.md).

## 5 — Embed the Angular widget

```bash
npm install chatbot-angular
```

```ts
// app.config.ts
import { ApplicationConfig } from "@angular/core";
import { CHATBOT_CONFIG } from "chatbot-angular";

export const appConfig: ApplicationConfig = {
  providers: [
    { provide: CHATBOT_CONFIG, useValue: { endpoint: "/api/chat", title: "Assistant" } },
  ],
};
```

```html
<!-- app.component.html -->
<cb-floating-chatbot />
```

Detail: [libraries/angular.md](libraries/angular.md).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `404` on `/chat` | Adapter not mounted | Confirm `mount(app, agent=bot)` ran before app startup |
| `401` from upstream LLM | API key missing or wrong | Check `echo $ANTHROPIC_API_KEY` |
| UI shows "Failed to send message" | Backend not reachable | Confirm CORS, port, and that the server is actually running |
| `Cannot find module 'react'` after npm install | React peer dep missing in host app | Install `react` and `react-dom` in your host app |
| Streaming hangs in nginx / cloudflare | Proxy buffering enabled | Set `X-Accel-Buffering: no` and disable proxy buffering — the Flask/FastAPI adapters already send this header |

## What to read next

- [Architecture](architecture.md) — how the pieces fit together
- [Wire protocol](wire-protocol.md) — the exact contract between client and server
- The library-specific guide for the stack you're integrating
