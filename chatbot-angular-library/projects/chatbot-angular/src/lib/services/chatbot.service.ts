import { Injectable, Signal, computed, effect, inject, signal } from '@angular/core';
import { CHATBOT_CONFIG, ChatbotConfig, DEFAULT_STORAGE_KEY_ANGULAR } from '../tokens/chatbot-config.token';
import { FilePart, Message, ToolCallState } from '../types';
import {
  PendingAttachment,
  attachmentPartsOnly,
  detachPendingAttachments,
  filesToAttachmentParts,
  pendingAttachmentsToParts,
  revokeAttachmentPreviews,
  withImageDefaultText,
} from '../utils/attachments';
import {
  getImageDisplaySrc,
  registerDisplayUrl,
  revokeAllDisplayUrls,
  revokeMessageDisplayUrls,
  stripClientFieldsFromRequest,
} from '../utils/attachment-display';
import { createId } from '../utils/id';
import { loadConversation, saveConversation } from '../utils/storage';
import { ThemeMode, ResolvedTheme, resolveTheme } from '../utils/theme';
import { ChatbotStreamError, streamChat } from '../transport/sse-client';

export interface SendMessageOptions {
  approvedToolIds?: string[];
  attachmentParts?: ReturnType<typeof pendingAttachmentsToParts>;
  silent?: boolean;
}

@Injectable()
export class ChatbotService {
  private readonly config: ChatbotConfig = inject(CHATBOT_CONFIG);

  // ── private writable signals ──────────────────────────────────────────────
  private readonly _isOpen = signal(false);
  private readonly _messages = signal<Message[]>([]);
  private readonly _conversationId = signal(createId('conv'));
  private readonly _isStreaming = signal(false);
  private readonly _isAwaitingReply = signal(false);
  private readonly _streamingMessageId = signal<string | null>(null);
  private readonly _streamingText = signal('');
  private readonly _streamingThinkingText = signal('');
  private readonly _toolCalls = signal<Record<string, ToolCallState>>({});
  private readonly _error = signal<string | null>(null);
  private readonly _theme = signal<ThemeMode>(this.config.theme ?? 'system');
  private readonly _resolvedTheme = signal<ResolvedTheme>(resolveTheme(this.config.theme ?? 'system'));
  private readonly _panelWide = signal(false);
  private readonly _embeddedPanelCollapsed = signal(false);
  private readonly _primaryColor = signal<string | undefined>(this.config.primaryColor);
  private readonly _attachmentsEnabled = signal<boolean>(this.config.attachments?.enabled !== false);
  private readonly _composerAttachments = signal<PendingAttachment[]>([]);
  private readonly _pendingFileParts = signal<FilePart[]>([]);

  private abortController: AbortController | null = null;

  // ── public read-only signals ──────────────────────────────────────────────
  readonly isOpen: Signal<boolean> = this._isOpen.asReadonly();
  readonly messages: Signal<Message[]> = this._messages.asReadonly();
  readonly conversationId: Signal<string> = this._conversationId.asReadonly();
  readonly isStreaming: Signal<boolean> = this._isStreaming.asReadonly();
  readonly isAwaitingReply: Signal<boolean> = this._isAwaitingReply.asReadonly();
  readonly streamingMessageId: Signal<string | null> = this._streamingMessageId.asReadonly();
  readonly streamingText: Signal<string> = this._streamingText.asReadonly();
  readonly streamingThinkingText: Signal<string> = this._streamingThinkingText.asReadonly();
  readonly toolCalls: Signal<Record<string, ToolCallState>> = this._toolCalls.asReadonly();
  readonly error: Signal<string | null> = this._error.asReadonly();
  readonly theme: Signal<ThemeMode> = this._theme.asReadonly();
  readonly resolvedTheme: Signal<ResolvedTheme> = this._resolvedTheme.asReadonly();
  readonly panelWide: Signal<boolean> = this._panelWide.asReadonly();
  readonly embeddedPanelCollapsed: Signal<boolean> = this._embeddedPanelCollapsed.asReadonly();
  readonly primaryColor: Signal<string | undefined> = this._primaryColor.asReadonly();
  readonly attachmentsEnabled: Signal<boolean> = this._attachmentsEnabled.asReadonly();
  readonly composerAttachments: Signal<PendingAttachment[]> = this._composerAttachments.asReadonly();
  readonly pendingFileParts: Signal<FilePart[]> = this._pendingFileParts.asReadonly();

  constructor() {
    // System theme watcher
    if (typeof window !== 'undefined' && this.config.theme === 'system') {
      const mql = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = (e: MediaQueryListEvent) => {
        if (this._theme() === 'system') {
          this._resolvedTheme.set(e.matches ? 'dark' : 'light');
        }
      };
      mql.addEventListener('change', handler);
    }

    // Persistence: hydrate on startup, save on change
    if (this.config.persist) {
      const key = this.config.storageKey ?? DEFAULT_STORAGE_KEY_ANGULAR;
      const stored = loadConversation(key);
      if (stored) {
        this._messages.set(stored.messages);
        this._conversationId.set(stored.conversationId);
      }
      effect(() => {
        saveConversation(key, {
          conversationId: this._conversationId(),
          messages: this._messages(),
        });
      });
    }
  }

  // ── actions ───────────────────────────────────────────────────────────────

  setOpen(open: boolean): void { this._isOpen.set(open); }
  toggleOpen(): void { this._isOpen.update(v => !v); }
  togglePanelWide(): void { this._panelWide.update(v => !v); }
  setEmbeddedPanelCollapsed(v: boolean): void { this._embeddedPanelCollapsed.set(v); }
  toggleEmbeddedPanelCollapsed(): void { this._embeddedPanelCollapsed.update(v => !v); }

  setTheme(theme: ThemeMode): void {
    this._theme.set(theme);
    this._resolvedTheme.set(theme === 'system' ? resolveTheme('system') : theme);
  }

  setPrimaryColor(color: string | undefined): void { this._primaryColor.set(color); }

  setAttachmentsEnabled(enabled: boolean): void {
    this._attachmentsEnabled.set(enabled);
    if (!enabled) this.clearComposerAttachments();
  }

  clearMessages(): void {
    for (const m of this._messages()) revokeMessageDisplayUrls(m);
    revokeAllDisplayUrls();
    revokeAttachmentPreviews(this._composerAttachments());
    this._messages.set([]);
    this._toolCalls.set({});
    this._conversationId.set(createId('conv'));
    this._error.set(null);
    this._streamingThinkingText.set('');
    this._isAwaitingReply.set(false);
    this._composerAttachments.set([]);
  }

  addComposerAttachments(items: PendingAttachment[]): void {
    this._composerAttachments.update(v => [...v, ...items]);
  }

  removeComposerAttachment(id: string): void {
    const item = this._composerAttachments().find(a => a.id === id);
    if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl);
    this._composerAttachments.update(v => v.filter(a => a.id !== id));
  }

  clearComposerAttachments(options?: { revoke?: boolean }): void {
    if (options?.revoke !== false) revokeAttachmentPreviews(this._composerAttachments());
    this._composerAttachments.set([]);
  }

  addPendingFilePart(part: FilePart): void {
    this._pendingFileParts.update(v => [...v, part]);
  }

  clearPendingFileParts(): void { this._pendingFileParts.set([]); }

  upsertToolCall(id: string, patch: Partial<ToolCallState>): void {
    this._toolCalls.update(calls => {
      const existing = calls[id];
      const messageId = patch.messageId ?? existing?.messageId ?? this._streamingMessageId() ?? undefined;
      const next: ToolCallState = {
        ...existing,
        id,
        name: existing?.name ?? patch.name ?? id,
        input: existing?.input ?? {},
        status: existing?.status ?? 'running',
        startedAt: existing?.startedAt ?? Date.now(),
        messageId,
        ...patch,
      };
      return { ...calls, [id]: next };
    });
  }

  stopStreaming(): void {
    this.abortController?.abort();
    this._finalizeStream();
  }

  async respondToToolApproval(toolId: string, approved: boolean): Promise<void> {
    this.upsertToolCall(toolId, {
      status: approved ? 'running' : 'denied',
      isError: !approved,
      output: approved ? undefined : 'Denied by user',
    });
    await this.config.onToolApproval?.(toolId, approved);
    if (approved) {
      await this.sendMessage('', { approvedToolIds: [toolId], silent: true });
    }
  }

  async sendMessage(text: string, options?: SendMessageOptions): Promise<void> {
    const trimmed = text.trim();
    const approvedToolIds = options?.approvedToolIds ?? [];
    const attachmentParts = options?.attachmentParts ?? [];
    if (!trimmed && approvedToolIds.length === 0 && attachmentParts.length === 0) return;
    if (this._isStreaming()) return;

    this._error.set(null);
    const userParts = withImageDefaultText(trimmed, attachmentParts);

    if (userParts.length > 0 && !options?.silent) {
      const userMessage: Message = {
        id: createId('msg'),
        role: 'user',
        parts: userParts,
        createdAt: Date.now(),
      };
      this._messages.update(msgs => [...msgs, userMessage]);
    }

    this._isAwaitingReply.set(true);

    const extraHeaders = this.config.getHeaders
      ? await this.config.getHeaders()
      : (this.config.headers ?? {});

    const body = {
      messages: this._messages(),
      conversationId: this._conversationId(),
      model: this.config.model,
      metadata: {
        ...(this.config.metadata ?? {}),
        ...(approvedToolIds.length > 0 ? { approvedToolIds } : {}),
      },
    };

    this.abortController = new AbortController();

    try {
      await streamChat({
        endpoint: this.config.endpoint,
        body,
        headers: extraHeaders,
        signal: this.abortController.signal,
        onEvent: (event) => this._handleEvent(event),
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        // user cancelled
      } else if (err instanceof ChatbotStreamError) {
        this._error.set(err.message);
      } else if (err instanceof Error) {
        this._error.set(err.message);
      } else {
        this._error.set('Failed to send message');
      }
    } finally {
      this._finalizeStream();
      this.abortController = null;
    }
  }

  // ── private helpers ───────────────────────────────────────────────────────

  private _handleEvent(event: { type: string; data: Record<string, unknown> }): void {
    switch (event.type) {
      case 'message_start': {
        const id = String(event.data['id'] ?? createId('msg'));
        this._isAwaitingReply.set(false);
        this._streamingMessageId.set(id);
        this._isStreaming.set(true);
        this._messages.update(msgs => [...msgs, {
          id,
          role: 'assistant',
          parts: [{ type: 'text', text: '' }],
          createdAt: Date.now(),
        }]);
        break;
      }
      case 'text_delta': {
        const thinking = this._streamingThinkingText().trim();
        const msgId = this._streamingMessageId();
        if (thinking && msgId) {
          this._updateMessage(msgId, m => ({ ...m, thinking: m.thinking ?? thinking }));
        }
        this._streamingText.update(t => t + String(event.data['delta'] ?? ''));
        break;
      }
      case 'thinking_delta':
        this._streamingThinkingText.update(t => t + String(event.data['delta'] ?? ''));
        break;
      case 'tool_call_start':
        this.upsertToolCall(String(event.data['id']), {
          name: String(event.data['name'] ?? ''),
          input: (event.data['input'] as Record<string, unknown>) ?? {},
          status: 'running',
        });
        break;
      case 'tool_call_delta':
        this.upsertToolCall(String(event.data['id']), {
          inputRaw: (this._toolCalls()[String(event.data['id'])]?.inputRaw ?? '') + String(event.data['inputDelta'] ?? ''),
        });
        break;
      case 'tool_call_end':
        this.upsertToolCall(String(event.data['id']), { status: 'running' });
        break;
      case 'tool_result':
        this.upsertToolCall(String(event.data['id']), {
          output: event.data['output'],
          isError: Boolean(event.data['isError']),
          status: event.data['isError'] ? 'error' : 'done',
        });
        break;
      case 'tool_approval_required':
        this.upsertToolCall(String(event.data['id']), {
          name: String(event.data['name'] ?? ''),
          input: (event.data['input'] as Record<string, unknown>) ?? {},
          status: 'approval',
        });
        break;
      case 'file_part':
        this.addPendingFilePart({
          type: 'file',
          name: String(event.data['name'] ?? 'file'),
          mimeType: String(event.data['mimeType'] ?? 'application/octet-stream'),
          data: String(event.data['data'] ?? ''),
        });
        break;
      case 'error':
        this._error.set(String(event.data['message'] ?? 'Unknown error'));
        break;
    }
  }

  private _finalizeStream(): void {
    const msgId = this._streamingMessageId();
    const text = this._streamingText();
    const thinking = this._streamingThinkingText().trim();
    const fileParts = this._pendingFileParts();

    if (msgId && (text || fileParts.length > 0)) {
      this._updateMessage(msgId, m => ({
        ...m,
        parts: [
          ...(text ? [{ type: 'text' as const, text }] : []),
          ...fileParts,
        ],
        ...(thinking ? { thinking: m.thinking ?? thinking } : {}),
      }));
    } else if (msgId && thinking) {
      this._updateMessage(msgId, m => ({ ...m, thinking: m.thinking ?? thinking }));
    } else if (msgId && !text && fileParts.length === 0) {
      this._messages.update(msgs => msgs.filter(m => m.id !== msgId));
    }

    this._pendingFileParts.set([]);
    this._streamingText.set('');
    this._streamingThinkingText.set('');
    this._streamingMessageId.set(null);
    this._isStreaming.set(false);
    this._isAwaitingReply.set(false);
  }

  private _updateMessage(id: string, updater: (m: Message) => Message): void {
    this._messages.update(msgs => msgs.map(m => m.id === id ? updater(m) : m));
  }
}
