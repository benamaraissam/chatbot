import { create } from "zustand";
import type { FilePart, ToolCallState } from "../types";
import {
  revokeAllDisplayUrls,
  revokeMessageDisplayUrls,
} from "../utils/attachmentDisplay";
import { revokeAttachmentPreviews } from "../utils/attachments";
import { createId } from "../utils/id";
import { resolveTheme } from "../utils/theme";
import type { ChatbotState, ThemeMode } from "./types";

export const createChatbotStore = (initialTheme: ThemeMode = "system") =>
  create<ChatbotState>((set, get) => ({
    isOpen: false,
    messages: [],
    conversationId: createId("conv"),
    isStreaming: false,
    isAwaitingReply: false,
    streamingMessageId: null,
    streamingText: "",
    streamingThinkingText: "",
    toolCalls: {},
    error: null,
    theme: initialTheme,
    resolvedTheme: resolveTheme(initialTheme),
    panelWide: false,
    embeddedPanelCollapsed: false,
    composerAttachments: [],
    pendingFileParts: [],

    setOpen: (open) => set({ isOpen: open }),
    toggleOpen: () => set({ isOpen: !get().isOpen }),
    togglePanelWide: () => set({ panelWide: !get().panelWide }),
    setEmbeddedPanelCollapsed: (embeddedPanelCollapsed) => set({ embeddedPanelCollapsed }),
    toggleEmbeddedPanelCollapsed: () =>
      set({ embeddedPanelCollapsed: !get().embeddedPanelCollapsed }),
    setTheme: (theme) =>
      set({
        theme,
        resolvedTheme: theme === "system" ? resolveTheme("system") : theme,
      }),
    setResolvedTheme: (resolvedTheme) => set({ resolvedTheme }),
    setMessages: (messages) => set({ messages }),
    addMessage: (message) => set({ messages: [...get().messages, message] }),
    updateMessage: (id, updater) =>
      set({
        messages: get().messages.map((m) => (m.id === id ? updater(m) : m)),
      }),
    setConversationId: (conversationId) => set({ conversationId }),
    setStreaming: (isStreaming) => set({ isStreaming }),
    setAwaitingReply: (isAwaitingReply) => set({ isAwaitingReply }),
    setStreamingMessageId: (streamingMessageId) => set({ streamingMessageId }),
    appendStreamingText: (delta) =>
      set({ streamingText: get().streamingText + delta }),
    appendThinkingText: (delta) =>
      set({ streamingThinkingText: get().streamingThinkingText + delta }),
    resetStreaming: () =>
      set({
        streamingText: "",
        streamingThinkingText: "",
        streamingMessageId: null,
        isStreaming: false,
        isAwaitingReply: false,
      }),
    upsertToolCall: (id, patch) => {
      const existing = get().toolCalls[id];
      const messageId =
        patch.messageId ?? existing?.messageId ?? get().streamingMessageId ?? undefined;
      const next: ToolCallState = {
        ...existing,
        id,
        name: existing?.name ?? patch.name ?? id,
        input: existing?.input ?? {},
        status: existing?.status ?? "running",
        startedAt: existing?.startedAt ?? Date.now(),
        messageId,
        ...patch,
      };
      set({ toolCalls: { ...get().toolCalls, [id]: next } });
    },
    setError: (error) => set({ error }),
    clearMessages: () => {
      for (const message of get().messages) revokeMessageDisplayUrls(message);
      revokeAllDisplayUrls();
      revokeAttachmentPreviews(get().composerAttachments);
      set({
        messages: [],
        toolCalls: {},
        conversationId: createId("conv"),
        error: null,
        streamingThinkingText: "",
        isAwaitingReply: false,
        composerAttachments: [],
      });
    },
    hydrate: (messages, conversationId) => set({ messages, conversationId }),
    addComposerAttachments: (items) =>
      set({ composerAttachments: [...get().composerAttachments, ...items] }),
    removeComposerAttachment: (id) => {
      const item = get().composerAttachments.find((a) => a.id === id);
      if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl);
      set({
        composerAttachments: get().composerAttachments.filter((a) => a.id !== id),
      });
    },
    clearComposerAttachments: (options) => {
      const items = get().composerAttachments;
      if (options?.revoke !== false) revokeAttachmentPreviews(items);
      set({ composerAttachments: [] });
    },
    addPendingFilePart: (part: FilePart) =>
      set({ pendingFileParts: [...get().pendingFileParts, part] }),
    clearPendingFileParts: () => set({ pendingFileParts: [] }),
  }));

export type ChatbotStore = ReturnType<typeof createChatbotStore>;
