# Wire protocol

The HTTP + Server-Sent Events (SSE) contract shared by the backend and every
frontend client. This is **the** integration contract — keep the Python
`protocol/schemas.py`, the React `src/types/protocol.ts`, and the Angular
`projects/chatbot-angular/src/lib/types/protocol.ts` in sync with this page.

Current protocol version: **`1`** (sent as the `X-Chatbot-Protocol-Version` header).

## HTTP endpoint

Every adapter mounts a single endpoint, configurable but conventionally:

```
POST /chat
Content-Type:                application/json
Accept:                      text/event-stream
X-Chatbot-Protocol-Version:  1
```

The request body is a JSON `ChatRequest`. The response is an SSE stream
terminated by a `done` event.

## Request shape

```ts
interface ChatRequest {
  messages: Message[];
  conversationId?: string;           // generated client-side if missing
  model?: string;                    // optional model override
  metadata?: Record<string, unknown>;
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  parts: MessagePart[];
  createdAt?: number;                // unix millis, optional
  thinking?: string;                 // persisted reasoning trace
}

type MessagePart = TextPart | ImagePart | FilePart;

interface TextPart   { type: "text";  text: string; }
interface ImagePart  { type: "image"; mimeType: string; data: string; name?: string; }
interface FilePart   { type: "file";  name: string; mimeType: string; data: string; }
```

Notes:

- `data` is **base64** with no `data:` URL prefix.
- Field names on the wire are **camelCase** (`mimeType`, `conversationId`).
  Python uses Pydantic aliases so internal snake_case round-trips correctly.
- The client may include a `displayUrl` on `ImagePart` for local rendering,
  but it is **stripped** from outgoing requests by both client transports
  (see `stripClientFieldsFromRequest`).

## Response — SSE event stream

The server returns `Content-Type: text/event-stream` and emits frames in the
canonical SSE format:

```
event: <event_name>
data: <json payload>

```

(blank line terminates the frame). Each frame's `data` is always JSON.

### Event taxonomy

| Event | Payload | When |
|---|---|---|
| `message_start` | `{ "id": "m_a1", "role": "assistant" }` | A new assistant message is about to stream |
| `text_delta` | `{ "delta": "..." }` | Incremental answer text |
| `thinking_delta` | `{ "delta": "..." }` | Incremental reasoning/thinking trace |
| `tool_call_start` | `{ "id": "t_1", "name": "get_weather", "input": {...} }` | Model invoked a tool |
| `tool_call_delta` | `{ "id": "t_1", "inputDelta": "..." }` | Streamed tool-input JSON chunk |
| `tool_call_end` | `{ "id": "t_1" }` | Tool input is complete (execution starts) |
| `tool_result` | `{ "id": "t_1", "output": {...}, "isError": false }` | Tool execution result |
| `tool_approval_required` | `{ "id": "t_1", "name": "...", "input": {...} }` | Tool needs human approval before running |
| `file_part` | `{ "name": "...", "mimeType": "...", "data": "<base64>" }` | Tool returned a binary artifact |
| `message_end` | `{}` | Assistant message is complete |
| `error` | `{ "message": "..." }` | Upstream or tool error — the stream still finishes with `done` |
| `done` | `{}` | Terminal frame — clients should close any active reader |

### Order guarantees

The server emits events in this order **per assistant turn**:

```
message_start
  ( thinking_delta* | text_delta* | tool_call_start
                                    ( tool_call_delta* )
                                    tool_call_end
                                    tool_result )*
message_end
done                                            ← always last
```

`error` may appear at any point; `done` is always emitted last, even after
an error — clients should always tear down on `done`.

### Tool-call ordering caveat

`tool_call_end` semantically marks "input is complete; the tool is now
executing". The runtime emits `tool_call_end` **before** `tool_result`.
Clients update tool status optimistically on `tool_result`, then on
`tool_call_end` they should **not** overwrite a terminal status. The
reference Angular service has been audited for this — see
[`ChatbotService._handleEvent`](../chatbot-angular-library/projects/chatbot-angular/src/lib/services/chatbot.service.ts).

## Decoder reference (Python)

The server-side codec is in
[`src/chatbot/protocol/sse.py`](../chatbot-python-library/src/chatbot/protocol/sse.py):

- `encode_sse_event(event_type, data)` — serialise a single frame
- `stream_event_to_sse(event)` — `StreamEvent` → SSE string
- `sse_stream(events)` — async iterator that wraps an upstream iterator,
  catches exceptions as `error` frames, always closes with `done`
- `SSEDecoder` — client-side helper, buffers partial frames across chunks

## Decoder reference (TypeScript)

Both frontend libraries implement an SSE consumer with the same shape:

- React: [`src/transport/sseClient.ts`](../chatbot-react-library/src/transport/sseClient.ts)
- Angular: [`projects/chatbot-angular/src/lib/transport/sse-client.ts`](../chatbot-angular-library/projects/chatbot-angular/src/lib/transport/sse-client.ts)

```ts
streamChat({
  endpoint: "/api/chat",
  body:   chatRequest,
  headers,
  signal,                                  // AbortController.signal
  onEvent: (event: ParsedSSEEvent) => {},  // callback per frame
});
```

`fetch` is used instead of `EventSource` because the request body is a JSON
payload (POST), and the response is consumed via the `ReadableStream` API.

## Versioning

- `PROTOCOL_VERSION` is exported from both Python (`protocol/schemas.py`)
  and TypeScript (`types/protocol.ts`).
- Clients send it in the `X-Chatbot-Protocol-Version` request header.
- Breaking changes bump the integer. Additive changes (new optional fields,
  new event types) do not require a bump if old clients can safely ignore
  them.

## Where to put a new event

If you add an event:

1. Add the dataclass in `core/events.py` with a `to_payload()` method.
2. Add the event name in `protocol/sse.py` (only if it isn't picked up
   automatically from the dataclass).
3. Add the literal type in both TypeScript `types/protocol.ts` files.
4. Update the table on this page.
5. Update the per-library decoder if the event needs custom handling.
