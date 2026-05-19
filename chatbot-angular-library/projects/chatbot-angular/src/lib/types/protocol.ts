/** Protocol v1 — aligned with chatbot-python-library protocol/schemas.py */

export const PROTOCOL_VERSION = '1';
export const PROTOCOL_HEADER = 'X-Chatbot-Protocol-Version';

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface TextPart {
  type: 'text';
  text: string;
}

export interface ImagePart {
  type: 'image';
  mimeType: string;
  /** Base64 payload (no data: URL prefix). */
  data: string;
  name?: string;
  /** Client-only blob URL for UI; stripped before API requests. */
  displayUrl?: string;
}

export interface FilePart {
  type: 'file';
  name: string;
  mimeType: string;
  /** Base64 payload (no data: URL prefix). */
  data: string;
}

export type MessagePart = TextPart | ImagePart | FilePart;

export interface Message {
  id: string;
  role: MessageRole;
  parts: MessagePart[];
  createdAt?: number;
  /** Persisted reasoning trace (shown collapsed after the turn completes). */
  thinking?: string;
}

export interface ChatRequest {
  messages: Message[];
  conversationId?: string;
  model?: string;
  metadata?: Record<string, unknown>;
}

export type SSEEventType =
  | 'message_start'
  | 'text_delta'
  | 'thinking_delta'
  | 'tool_call_start'
  | 'tool_call_delta'
  | 'tool_call_end'
  | 'tool_result'
  | 'tool_approval_required'
  | 'file_part'
  | 'message_end'
  | 'error'
  | 'done';

export interface ParsedSSEEvent {
  type: SSEEventType;
  data: Record<string, unknown>;
}

export interface ToolCallState {
  id: string;
  name: string;
  input: Record<string, unknown>;
  inputRaw?: string;
  status: 'running' | 'done' | 'error' | 'approval' | 'denied';
  output?: unknown;
  isError?: boolean;
  messageId?: string;
  startedAt?: number;
}
