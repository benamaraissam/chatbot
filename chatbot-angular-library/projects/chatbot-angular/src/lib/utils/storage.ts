import type { Message } from '../types';

export const DEFAULT_STORAGE_KEY = 'chatbot-angular:conversation';

export interface StoredConversation {
  conversationId: string;
  messages: Message[];
}

export function loadConversation(key: string): StoredConversation | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as StoredConversation;
  } catch {
    return null;
  }
}

export function saveConversation(key: string, data: StoredConversation): void {
  if (typeof localStorage === 'undefined') return;
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch {
    // storage full or unavailable
  }
}
