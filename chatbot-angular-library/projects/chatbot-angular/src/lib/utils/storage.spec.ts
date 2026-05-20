import {
  DEFAULT_STORAGE_KEY,
  loadConversation,
  saveConversation,
} from './storage';

const KEY = 'chatbot-angular-test:conv';

describe('conversation storage (Angular)', () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => localStorage.clear());

  it('exports a sensible default storage key', () => {
    expect(DEFAULT_STORAGE_KEY).toBe('chatbot-angular:conversation');
  });

  it('returns null when nothing is stored under the key', () => {
    expect(loadConversation(KEY)).toBeNull();
  });

  it('round-trips a simple conversation', () => {
    saveConversation(KEY, {
      conversationId: 'c1',
      messages: [
        { id: 'm_1', role: 'user', parts: [{ type: 'text', text: 'hi' }] },
      ],
    });
    const loaded = loadConversation(KEY);
    expect(loaded).not.toBeNull();
    expect(loaded!.conversationId).toBe('c1');
    expect(loaded!.messages.length).toBe(1);
    expect(loaded!.messages[0].id).toBe('m_1');
  });

  it('returns null on malformed JSON instead of throwing', () => {
    localStorage.setItem(KEY, 'not-json{');
    expect(loadConversation(KEY)).toBeNull();
  });

  it('overwrites previous data when saving again under the same key', () => {
    saveConversation(KEY, { conversationId: 'c1', messages: [] });
    saveConversation(KEY, {
      conversationId: 'c2',
      messages: [
        { id: 'm_1', role: 'assistant', parts: [{ type: 'text', text: 'ok' }] },
      ],
    });
    const loaded = loadConversation(KEY);
    expect(loaded!.conversationId).toBe('c2');
    expect(loaded!.messages.length).toBe(1);
  });
});
