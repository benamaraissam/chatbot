import type { Message, ToolCallState } from "../types";
import type { PendingAttachment } from "../utils/attachments";

export type ThemeMode = "light" | "dark" | "system";

export interface ChatbotConfig {
  endpoint: string;
  headers?: Record<string, string>;
  getHeaders?: () => Record<string, string> | Promise<Record<string, string>>;
  model?: string;
  metadata?: Record<string, unknown>;
  storageKey?: string;
  persist?: boolean;
  title?: string;
  placeholder?: string;
  theme?: ThemeMode;
  /**
   * Brand primary color (hex `#0d9488` or `rgb(13, 148, 136)`).
   * Sets `--cb-primary` and related tokens on the chat UI.
   */
  primaryColor?: string;
  /** Show header theme toggle. Default: `true` only when `theme="system"`. */
  allowThemeToggle?: boolean;
  /** Called when user approves or denies a tool (status `approval`). */
  onToolApproval?: (toolId: string, approved: boolean) => void | Promise<void>;
  /** Suggested prompts shown in empty state */
  suggestions?: string[];
  /**
   * How the provider root participates in page layout.
   * - `overlay` (default): fixed layer for FloatingChatbot; does not cover the app.
   * - `block`: normal flow (embed ChatWindow in your own layout).
   */
  hostLayout?: "overlay" | "block";
  /** File and image attachments in the composer. */
  attachments?: {
    /** Default `true`. */
    enabled?: boolean;
    /** Max files per message. Default `5`. */
    maxCount?: number;
    /** Max bytes per file. Default 5 MB. */
    maxSizeBytes?: number;
    /** Input `accept` attribute. */
    accept?: string;
  };
}

export interface ChatbotState {
  isOpen: boolean;
  messages: Message[];
  conversationId: string;
  isStreaming: boolean;
  /** True from send until `message_start` (waiting on the network). */
  isAwaitingReply: boolean;
  streamingMessageId: string | null;
  streamingText: string;
  streamingThinkingText: string;
  toolCalls: Record<string, ToolCallState>;
  error: string | null;
  theme: ThemeMode;
  resolvedTheme: "light" | "dark";
  /** Desktop panel at 2× default width (800px vs 400px). */
  panelWide: boolean;
  /** Embedded sidebar dock collapsed to a narrow rail. */
  embeddedPanelCollapsed: boolean;
  /** Files/images staged in the composer before send. */
  composerAttachments: PendingAttachment[];

  setOpen: (open: boolean) => void;
  toggleOpen: () => void;
  togglePanelWide: () => void;
  setEmbeddedPanelCollapsed: (collapsed: boolean) => void;
  toggleEmbeddedPanelCollapsed: () => void;
  setTheme: (theme: ThemeMode) => void;
  setResolvedTheme: (theme: "light" | "dark") => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updater: (msg: Message) => Message) => void;
  setConversationId: (id: string) => void;
  setStreaming: (streaming: boolean) => void;
  setAwaitingReply: (awaiting: boolean) => void;
  setStreamingMessageId: (id: string | null) => void;
  appendStreamingText: (delta: string) => void;
  appendThinkingText: (delta: string) => void;
  resetStreaming: () => void;
  upsertToolCall: (id: string, patch: Partial<ToolCallState>) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
  hydrate: (messages: Message[], conversationId: string) => void;
  addComposerAttachments: (items: PendingAttachment[]) => void;
  removeComposerAttachment: (id: string) => void;
  clearComposerAttachments: (options?: { revoke?: boolean }) => void;
}
