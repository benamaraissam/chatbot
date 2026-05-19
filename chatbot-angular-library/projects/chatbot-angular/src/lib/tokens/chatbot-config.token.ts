import { InjectionToken } from '@angular/core';
import type { ThemeMode } from '../utils/theme';

export interface ChatbotConfig {
  /** Backend SSE endpoint, e.g. '/api/chat' */
  endpoint: string;
  /** Static extra headers */
  headers?: Record<string, string>;
  /** Async header factory (called per request) */
  getHeaders?: () => Record<string, string> | Promise<Record<string, string>>;
  model?: string;
  metadata?: Record<string, unknown>;
  /** localStorage key for persistence. Default: 'chatbot-angular:conversation' */
  storageKey?: string;
  /** Persist conversation to localStorage. Default: false */
  persist?: boolean;
  title?: string;
  placeholder?: string;
  theme?: ThemeMode;
  primaryColor?: string;
  allowThemeToggle?: boolean;
  onToolApproval?: (toolId: string, approved: boolean) => void | Promise<void>;
  suggestions?: string[];
  hostLayout?: 'overlay' | 'block';
  attachments?: {
    enabled?: boolean;
    maxCount?: number;
    maxSizeBytes?: number;
    accept?: string;
  };
}

export const CHATBOT_CONFIG = new InjectionToken<ChatbotConfig>('CHATBOT_CONFIG');
export const DEFAULT_STORAGE_KEY_ANGULAR = 'chatbot-angular:conversation';
