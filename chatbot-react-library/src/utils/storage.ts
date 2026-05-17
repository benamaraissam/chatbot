import type { Message, MessagePart } from "../types";

const DEFAULT_KEY = "chatbot-react:conversation";

/** Max base64 chars to persist per attachment (avoids localStorage quota wiping state). */
const MAX_PERSISTED_DATA_CHARS = 80_000;

export interface StoredConversation {
  conversationId: string;
  messages: Message[];
}

function stripPartForStorage(part: MessagePart): MessagePart {
  if (part.type === "image") {
    const { displayUrl: _d, ...base } = part;
    if (base.data.length <= MAX_PERSISTED_DATA_CHARS) return base;
    return { ...base, data: "" };
  }
  if (part.type === "file") {
    if (part.data.length <= MAX_PERSISTED_DATA_CHARS) return part;
    return { ...part, data: "" };
  }
  return part;
}

function stripMessageForStorage(message: Message): Message {
  return {
    ...message,
    parts: message.parts.map(stripPartForStorage),
  };
}

export function loadConversation(key: string): StoredConversation | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as StoredConversation;
  } catch {
    return null;
  }
}

export function saveConversation(key: string, data: StoredConversation): void {
  if (typeof window === "undefined") return;
  try {
    const slim: StoredConversation = {
      conversationId: data.conversationId,
      messages: data.messages.map(stripMessageForStorage),
    };
    localStorage.setItem(key, JSON.stringify(slim));
  } catch {
    /* quota exceeded — ignore; in-memory state still has full attachments */
  }
}

export function clearConversation(key: string): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(key);
}

export { DEFAULT_KEY as DEFAULT_STORAGE_KEY };
