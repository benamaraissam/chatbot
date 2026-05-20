import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// We import lazily inside each test so we can stub fetch first.
const sseModule = () => import("./sseClient");

function readableFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(enc.encode(c));
      controller.close();
    },
  });
}

function fakeResponse(opts: {
  status?: number;
  body?: ReadableStream<Uint8Array> | null;
  text?: string;
}): Response {
  const status = opts.status ?? 200;
  const init: ResponseInit = { status };
  const r = new Response(opts.body ?? null, init);
  if (opts.text !== undefined) {
    (r as unknown as { text: () => Promise<string> }).text = () =>
      Promise.resolve(opts.text!);
  }
  return r;
}

const minimalRequest = {
  conversationId: "conv_test",
  messages: [{ id: "m_1", role: "user", parts: [{ type: "text", text: "hi" }] }],
};

describe("streamChat (React)", () => {
  let originalFetch: typeof fetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("throws a stream error with the HTTP status on a non-2xx response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      fakeResponse({ status: 502, body: null, text: "bad gateway" }),
    ) as unknown as typeof fetch;

    const { streamChat, ChatbotStreamError } = await sseModule();
    await expect(
      streamChat({
        endpoint: "/api/chat",
        body: minimalRequest as never,
        onEvent: () => {},
      }),
    ).rejects.toBeInstanceOf(ChatbotStreamError);
  });

  it("parses a simple SSE stream into typed events", async () => {
    const sse =
      "event: text_delta\n" +
      'data: {"delta":"hello"}\n\n' +
      "event: done\n" +
      "data: {}\n\n";
    globalThis.fetch = vi.fn().mockResolvedValue(
      fakeResponse({ status: 200, body: readableFromChunks([sse]) }),
    ) as unknown as typeof fetch;

    const { streamChat } = await sseModule();
    const types: string[] = [];
    await streamChat({
      endpoint: "/api/chat",
      body: minimalRequest as never,
      onEvent: (ev) => types.push(ev.type),
    });
    expect(types).toEqual(["text_delta", "done"]);
  });
});
