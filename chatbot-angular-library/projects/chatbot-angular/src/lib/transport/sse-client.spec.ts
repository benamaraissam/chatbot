import { ChatbotStreamError, streamChat } from './sse-client';
import type { ChatRequest } from '../types';

/** Helpers to build a fake fetch response with a streaming body. */
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
  ok?: boolean;
  status?: number;
  body?: ReadableStream<Uint8Array> | null;
  text?: string;
}): Response {
  const status = opts.status ?? 200;
  const init: ResponseInit = { status };
  // ReadableStream-backed Response — supported in modern browsers, which is
  // also where the production transport runs.
  const r = new Response(opts.body ?? null, init);
  // Allow tests that want a text() fallback to override it cheaply.
  if (opts.text !== undefined) {
    (r as unknown as { text: () => Promise<string> }).text = () =>
      Promise.resolve(opts.text!);
  }
  return r;
}

const minimalRequest: ChatRequest = {
  conversationId: 'conv_test',
  messages: [{ id: 'm_1', role: 'user', parts: [{ type: 'text', text: 'hi' }] }],
} as unknown as ChatRequest;

describe('streamChat', () => {
  let originalFetch: typeof fetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('throws ChatbotStreamError with the HTTP status on a non-2xx response', async () => {
    globalThis.fetch = jasmine.createSpy('fetch').and.resolveTo(
      fakeResponse({ status: 502, body: null, text: 'bad gateway' }),
    );

    let caught: unknown = null;
    try {
      await streamChat({
        endpoint: '/api/chat',
        body: minimalRequest,
        onEvent: () => {},
      });
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ChatbotStreamError);
    const e = caught as ChatbotStreamError;
    expect(e.status).toBe(502);
    expect(e.code).toBe('http_error');
  });

  it('throws ChatbotStreamError when the response has no body', async () => {
    globalThis.fetch = jasmine.createSpy('fetch').and.resolveTo(
      fakeResponse({ status: 200, body: null }),
    );

    let caught: unknown = null;
    try {
      await streamChat({
        endpoint: '/api/chat',
        body: minimalRequest,
        onEvent: () => {},
      });
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ChatbotStreamError);
    expect((caught as ChatbotStreamError).code).toBe('no_body');
  });

  it('parses a simple SSE stream into parsed events', async () => {
    const sse =
      'event: text_delta\n' +
      'data: {"delta":"hello"}\n\n' +
      'event: done\n' +
      'data: {}\n\n';
    globalThis.fetch = jasmine.createSpy('fetch').and.resolveTo(
      fakeResponse({ status: 200, body: readableFromChunks([sse]) }),
    );

    const received: string[] = [];
    await streamChat({
      endpoint: '/api/chat',
      body: minimalRequest,
      onEvent: (ev) => {
        received.push(ev.type);
      },
    });

    expect(received).toEqual(['text_delta', 'done']);
  });
});
