import { TestBed } from '@angular/core/testing';
import { CHATBOT_CONFIG, ChatbotConfig } from '../tokens/chatbot-config.token';
import { ChatbotService } from './chatbot.service';

function configFor(overrides: Partial<ChatbotConfig> = {}): ChatbotConfig {
  return {
    endpoint: '/api/chat',
    persist: false,
    theme: 'light',
    ...overrides,
  };
}

describe('ChatbotService', () => {
  function makeService(config?: Partial<ChatbotConfig>): ChatbotService {
    TestBed.configureTestingModule({
      providers: [
        { provide: CHATBOT_CONFIG, useValue: configFor(config) },
        ChatbotService,
      ],
    });
    return TestBed.inject(ChatbotService);
  }

  it('initializes with an empty conversation in the closed state', () => {
    const svc = makeService();
    expect(svc.isOpen()).toBeFalse();
    expect(svc.messages()).toEqual([]);
    expect(svc.isStreaming()).toBeFalse();
  });

  it('assigns a non-empty conversation id at construction', () => {
    const svc = makeService();
    const id = svc.conversationId();
    expect(typeof id).toBe('string');
    expect(id.length).toBeGreaterThan(0);
    expect(id).toMatch(/^conv_/);
  });

  it('resolves the initial theme from the configured mode', () => {
    const svc = makeService({ theme: 'dark' });
    expect(svc.resolvedTheme()).toBe('dark');
  });
});
