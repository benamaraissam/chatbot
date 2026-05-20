import { TestBed } from '@angular/core/testing';
import { CHATBOT_CONFIG, ChatbotConfig } from '../tokens/chatbot-config.token';
import { ChatbotService } from './chatbot.service';

/**
 * sendMessage flow spec — mocks fetch with a complete SSE script so the
 * service walks through every event handler (message_start, text_delta,
 * thinking_delta, tool_call_*, tool_result, message_end, done). This single
 * spec exercises the largest single block of uncovered code in the library.
 */

function readable(frames: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const f of frames) controller.enqueue(enc.encode(f));
      controller.close();
    },
  });
}

function makeService(config: Partial<ChatbotConfig> = {}): ChatbotService {
  // Reset TestBed first so callers can reconfigure within a single test
  // (e.g., when they need a service built with custom config).
  TestBed.resetTestingModule();
  TestBed.configureTestingModule({
    providers: [
      {
        provide: CHATBOT_CONFIG,
        useValue: { endpoint: '/api/chat', persist: false, ...config },
      },
      ChatbotService,
    ],
  });
  return TestBed.inject(ChatbotService);
}

describe('ChatbotService.sendMessage — full SSE flow', () => {
  let originalFetch: typeof fetch;
  let svc: ChatbotService;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    svc = makeService();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('appends the user message and the assistant reply after a clean stream', async () => {
    const frames = [
      'event: message_start\ndata: {"id":"m_a","role":"assistant"}\n\n',
      'event: text_delta\ndata: {"delta":"Hello "}\n\n',
      'event: text_delta\ndata: {"delta":"world"}\n\n',
      'event: message_end\ndata: {}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    globalThis.fetch = jasmine
      .createSpy('fetch')
      .and.resolveTo(new Response(readable(frames), { status: 200 }));

    await svc.sendMessage('hi');

    const messages = svc.messages();
    expect(messages.length).toBe(2);
    expect(messages[0].role).toBe('user');
    expect(messages[1].role).toBe('assistant');
    expect(
      (messages[1].parts[0] as { text: string }).text,
    ).toContain('Hello world');
    // After the stream ends, awaiting and streaming flags are cleared.
    expect(svc.isStreaming()).toBeFalse();
    expect(svc.isAwaitingReply()).toBeFalse();
  });

  it('handles thinking deltas without appending them to the visible text', async () => {
    const frames = [
      'event: message_start\ndata: {"id":"m_b","role":"assistant"}\n\n',
      'event: thinking_delta\ndata: {"delta":"Working through it..."}\n\n',
      'event: text_delta\ndata: {"delta":"Result"}\n\n',
      'event: message_end\ndata: {}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    globalThis.fetch = jasmine
      .createSpy('fetch')
      .and.resolveTo(new Response(readable(frames), { status: 200 }));

    await svc.sendMessage('think please');
    const last = svc.messages().at(-1)!;
    expect((last.parts[0] as { text: string }).text).toBe('Result');
    // Thinking text travels via the message's `thinking` field after the turn.
    expect(last.thinking).toContain('Working through it');
  });

  it('registers a tool call and stores its result', async () => {
    // tool_call_end MUST come before tool_result — the service's
    // tool_call_end handler resets the status to "running", so if it ran
    // after tool_result it would clobber the "done" status.
    const frames = [
      'event: message_start\ndata: {"id":"m_c","role":"assistant"}\n\n',
      'event: tool_call_start\ndata: {"id":"t_1","name":"get_weather","input":{"city":"Paris"}}\n\n',
      'event: tool_call_end\ndata: {"id":"t_1"}\n\n',
      'event: tool_result\ndata: {"id":"t_1","output":{"temp_c":22}}\n\n',
      'event: text_delta\ndata: {"delta":"22°C in Paris."}\n\n',
      'event: message_end\ndata: {}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    globalThis.fetch = jasmine
      .createSpy('fetch')
      .and.resolveTo(new Response(readable(frames), { status: 200 }));

    await svc.sendMessage('weather in Paris');
    const tools = svc.toolCalls();
    expect(tools['t_1']).toBeDefined();
    expect(tools['t_1'].name).toBe('get_weather');
    expect(tools['t_1'].status).toBe('done');
    expect(tools['t_1'].output).toEqual({ temp_c: 22 });
  });

  it('returns immediately when called with an empty text and no attachments', async () => {
    const spy = jasmine.createSpy('fetch');
    globalThis.fetch = spy;
    await svc.sendMessage('');
    expect(spy).not.toHaveBeenCalled();
    expect(svc.messages()).toEqual([]);
  });

  it('exposes the configured extra headers via getHeaders()', async () => {
    svc = makeService({
      getHeaders: () => ({ 'X-Tenant': 't1', Authorization: 'Bearer xxx' }),
    });
    const spy = jasmine
      .createSpy('fetch')
      .and.resolveTo(
        new Response(
          readable([
            'event: message_start\ndata: {"id":"m_h","role":"assistant"}\n\n',
            'event: text_delta\ndata: {"delta":"ok"}\n\n',
            'event: message_end\ndata: {}\n\n',
            'event: done\ndata: {}\n\n',
          ]),
          { status: 200 },
        ),
      );
    globalThis.fetch = spy;

    await svc.sendMessage('hi');

    // First call argument is the URL; second is the init bag with headers.
    const [, init] = spy.calls.mostRecent().args as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers['X-Tenant']).toBe('t1');
    expect(headers['Authorization']).toBe('Bearer xxx');
  });
});
