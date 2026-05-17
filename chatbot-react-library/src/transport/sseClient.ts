import {
  PROTOCOL_HEADER,
  PROTOCOL_VERSION,
  type ChatRequest,
  type ParsedSSEEvent,
  type SSEEventType,
} from "../types";
import { stripClientFieldsFromRequest } from "../utils/attachmentDisplay";

export interface StreamChatOptions {
  endpoint: string;
  body: ChatRequest;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  onEvent: (event: ParsedSSEEvent) => void;
}

export class ChatbotStreamError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ChatbotStreamError";
  }
}

export async function streamChat({
  endpoint,
  body,
  headers = {},
  signal,
  onEvent,
}: StreamChatOptions): Promise<void> {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      [PROTOCOL_HEADER]: PROTOCOL_VERSION,
      ...headers,
    },
    body: JSON.stringify(stripClientFieldsFromRequest(body)),
    signal,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ChatbotStreamError(
      text || `HTTP ${response.status}`,
      "http_error",
      response.status,
    );
  }

  if (!response.body) {
    throw new ChatbotStreamError("No response body", "no_body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const parsed = parseSSEFrame(frame);
      if (parsed) {
        onEvent(parsed);
        if (parsed.type === "done") return;
      }
    }
  }

  if (buffer.trim()) {
    const parsed = parseSSEFrame(buffer);
    if (parsed) onEvent(parsed);
  }
}

function parseSSEFrame(block: string): ParsedSSEEvent | null {
  let type: SSEEventType | null = null;
  let data: Record<string, unknown> = {};

  for (const line of block.trim().split("\n")) {
    if (line.startsWith("event:")) {
      type = line.slice(6).trim() as SSEEventType;
    } else if (line.startsWith("data:")) {
      const raw = line.slice(5).trim();
      try {
        data = raw ? (JSON.parse(raw) as Record<string, unknown>) : {};
      } catch {
        data = { raw };
      }
    }
  }

  if (!type) return null;
  return { type, data };
}
