import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";
import { ChatbotStreamError, streamChat } from "../transport";
import type { Message, ParsedSSEEvent } from "../types";
import { createId } from "../utils/id";
import {
  DEFAULT_STORAGE_KEY,
  loadConversation,
  saveConversation,
} from "../utils/storage";
import { ChatbotContext, type ChatbotContextValue, type SendMessageOptions } from "./context";
import { createChatbotStore } from "./store";
import type { ChatbotConfig } from "./types";
import { withImageDefaultText } from "../utils/attachments";
import { buildPrimaryColorStyle } from "../utils/primaryColor";
import { resolveTheme } from "../utils/theme";

export interface ChatbotProviderProps extends ChatbotConfig {
  children: ReactNode;
}

export function ChatbotProvider({
  children,
  endpoint,
  headers,
  getHeaders,
  model,
  metadata,
  storageKey = DEFAULT_STORAGE_KEY,
  persist = true,
  theme = "system",
  primaryColor,
  allowThemeToggle,
  onToolApproval,
  suggestions,
  title,
  placeholder,
  attachments,
  hostLayout = "overlay",
}: ChatbotProviderProps) {
  const resolvedAllowThemeToggle = allowThemeToggle ?? theme === "system";

  const config = useMemo<ChatbotConfig>(
    () => ({
      endpoint,
      headers,
      getHeaders,
      model,
      metadata,
      storageKey,
      persist,
      theme,
      primaryColor,
      allowThemeToggle: resolvedAllowThemeToggle,
      onToolApproval,
      suggestions,
      title,
      placeholder,
      attachments,
      hostLayout,
    }),
    [
      endpoint,
      headers,
      getHeaders,
      model,
      metadata,
      storageKey,
      persist,
      theme,
      primaryColor,
      resolvedAllowThemeToggle,
      onToolApproval,
      suggestions,
      title,
      placeholder,
      attachments,
      hostLayout,
    ],
  );

  const storeRef = useRef<ReturnType<typeof createChatbotStore>>();
  if (!storeRef.current) {
    storeRef.current = createChatbotStore(theme);
  }
  const store = storeRef.current;

  const attachmentsEnabled = attachments?.enabled !== false;
  useEffect(() => {
    if (!attachmentsEnabled) {
      store.getState().clearComposerAttachments();
    }
  }, [attachmentsEnabled, store]);

  const abortRef = useRef<AbortController | null>(null);
  const hydratedRef = useRef(false);

  const resolvedTheme = store((s) => s.resolvedTheme);
  const setResolvedTheme = store((s) => s.setResolvedTheme);
  const embeddedPanelCollapsed = store((s) => s.embeddedPanelCollapsed);

  // Apply theme from config (light | dark | system)
  useEffect(() => {
    store.getState().setTheme(theme);
    store.getState().setResolvedTheme(resolveTheme(theme));
  }, [theme, store]);

  // Follow OS when theme="system"
  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setResolvedTheme(resolveTheme("system"));
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [theme, setResolvedTheme]);

  useEffect(() => {
    if (!persist || hydratedRef.current) return;
    hydratedRef.current = true;
    const saved = loadConversation(storageKey);
    if (saved) {
      store.getState().hydrate(saved.messages, saved.conversationId);
    }
  }, [persist, storageKey, store]);

  useEffect(() => {
    if (!persist) return;
    const unsub = store.subscribe((state) => {
      saveConversation(storageKey, {
        conversationId: state.conversationId,
        messages: state.messages,
      });
    });
    return unsub;
  }, [persist, storageKey, store]);

  const handleEvent = useCallback(
    (event: ParsedSSEEvent) => {
      const s = store.getState();
      switch (event.type) {
        case "message_start": {
          const id = String(event.data.id ?? createId("msg"));
          s.setAwaitingReply(false);
          s.setStreamingMessageId(id);
          s.setStreaming(true);
          s.addMessage({
            id,
            role: "assistant",
            parts: [{ type: "text", text: "" }],
            createdAt: Date.now(),
          });
          break;
        }
        case "text_delta": {
          const thinking = s.streamingThinkingText.trim();
          const msgId = s.streamingMessageId;
          if (thinking && msgId) {
            s.updateMessage(msgId, (m) => ({
              ...m,
              thinking: m.thinking ?? thinking,
            }));
          }
          s.appendStreamingText(String(event.data.delta ?? ""));
          break;
        }
        case "thinking_delta":
          s.appendThinkingText(String(event.data.delta ?? ""));
          break;
        case "tool_call_start":
          s.upsertToolCall(String(event.data.id), {
            name: String(event.data.name ?? ""),
            input: (event.data.input as Record<string, unknown>) ?? {},
            status: "running",
          });
          break;
        case "tool_call_delta":
          s.upsertToolCall(String(event.data.id), {
            inputRaw:
              (s.toolCalls[String(event.data.id)]?.inputRaw ?? "") +
              String(event.data.inputDelta ?? ""),
          });
          break;
        case "tool_call_end":
          s.upsertToolCall(String(event.data.id), { status: "running" });
          break;
        case "tool_result":
          s.upsertToolCall(String(event.data.id), {
            output: event.data.output,
            isError: Boolean(event.data.isError),
            status: event.data.isError ? "error" : "done",
          });
          break;
        case "tool_approval_required":
          s.upsertToolCall(String(event.data.id), {
            name: String(event.data.name ?? ""),
            input: (event.data.input as Record<string, unknown>) ?? {},
            status: "approval",
          });
          break;
        case "file_part":
          s.addPendingFilePart({
            type: "file",
            name: String(event.data.name ?? "file"),
            mimeType: String(event.data.mimeType ?? "application/octet-stream"),
            data: String(event.data.data ?? ""),
          });
          break;
        case "message_end":
          break;
        case "error":
          s.setError(String(event.data.message ?? "Unknown error"));
          break;
        case "done":
          break;
      }
    },
    [store],
  );

  const finalizeStream = useCallback(() => {
    const s = store.getState();
    const msgId = s.streamingMessageId;
    const text = s.streamingText;
    const thinking = s.streamingThinkingText.trim();
    const fileParts = s.pendingFileParts;
    if (msgId && (text || fileParts.length > 0)) {
      s.updateMessage(msgId, (m) => ({
        ...m,
        parts: [
          ...(text ? [{ type: "text" as const, text }] : []),
          ...fileParts,
        ],
        ...(thinking ? { thinking: m.thinking ?? thinking } : {}),
      }));
    } else if (msgId && thinking) {
      s.updateMessage(msgId, (m) => ({
        ...m,
        thinking: m.thinking ?? thinking,
      }));
    } else if (msgId && !text && fileParts.length === 0) {
      s.setMessages(s.messages.filter((m) => m.id !== msgId));
    }
    s.clearPendingFileParts();
    s.resetStreaming();
    s.setStreaming(false);
  }, [store]);

  const sendMessage = useCallback(
    async (
      text: string,
      options?: SendMessageOptions,
    ) => {
      const trimmed = text.trim();
      const approvedToolIds = options?.approvedToolIds ?? [];
      const attachmentParts = options?.attachmentParts ?? [];
      if (!trimmed && approvedToolIds.length === 0 && attachmentParts.length === 0) {
        return;
      }

      const s = store.getState();
      if (s.isStreaming) return;

      s.setError(null);
      const userParts = withImageDefaultText(trimmed, attachmentParts);
      if (userParts.length > 0 && !options?.silent) {
        const userMessage: Message = {
          id: createId("msg"),
          role: "user",
          parts: userParts,
          createdAt: Date.now(),
        };
        s.addMessage(userMessage);
      }

      const allMessages = [...store.getState().messages];
      const requestMetadata = {
        ...metadata,
        ...(approvedToolIds.length > 0
          ? { approvedToolIds, approved_tool_ids: approvedToolIds }
          : {}),
      };
      const extraHeaders = getHeaders ? await getHeaders() : {};
      abortRef.current = new AbortController();
      s.setAwaitingReply(true);

      try {
        await streamChat({
          endpoint,
          body: {
            messages: allMessages,
            conversationId: s.conversationId,
            model,
            metadata: requestMetadata,
          },
          headers: { ...headers, ...extraHeaders },
          signal: abortRef.current.signal,
          onEvent: handleEvent,
        });
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          /* user cancelled */
        } else if (err instanceof ChatbotStreamError) {
          s.setError(err.message);
        } else if (err instanceof Error) {
          s.setError(err.message);
        } else {
          s.setError("Failed to send message");
        }
      } finally {
        finalizeStream();
        abortRef.current = null;
      }
    },
    [
      endpoint,
      finalizeStream,
      getHeaders,
      handleEvent,
      headers,
      metadata,
      model,
      store,
    ],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    finalizeStream();
  }, [finalizeStream]);

  const respondToToolApproval = useCallback(
    async (toolId: string, approved: boolean) => {
      const s = store.getState();
      s.upsertToolCall(toolId, {
        status: approved ? "running" : "denied",
        isError: !approved,
        output: approved ? undefined : "Denied by user",
      });
      await config.onToolApproval?.(toolId, approved);
      if (approved) {
        await sendMessage("", { approvedToolIds: [toolId], silent: true });
      }
    },
    [config, sendMessage, store],
  );

  const primaryStyle = useMemo(
    () =>
      primaryColor ? buildPrimaryColorStyle(primaryColor, resolvedTheme) : undefined,
    [primaryColor, resolvedTheme],
  );

  const value = useMemo<ChatbotContextValue>(
    () => ({ config, store, sendMessage, stopStreaming, respondToToolApproval }),
    [config, store, sendMessage, stopStreaming, respondToToolApproval],
  );

  return (
    <ChatbotContext.Provider value={value}>
      <div
        className={`cb-root${
          hostLayout === "overlay"
            ? " cb-root--overlay"
            : hostLayout === "block"
              ? " cb-root--block"
              : ""
        }`}
        data-cb-theme={resolvedTheme}
        data-cb-panel-collapsed={
          hostLayout === "block" && embeddedPanelCollapsed ? "true" : undefined
        }
        style={primaryStyle}
      >
        {children}
      </div>
    </ChatbotContext.Provider>
  );
}
