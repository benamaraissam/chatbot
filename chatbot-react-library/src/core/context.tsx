import { createContext, useContext } from "react";
import type { ChatbotStore } from "./store";
import type { MessagePart } from "../types";
import type { ChatbotConfig } from "./types";

export interface SendMessageOptions {
  /** Tool IDs approved in a human-in-the-loop step (sent via request metadata). */
  approvedToolIds?: string[];
  /** Skip adding a user message (e.g. approval-only resume). */
  silent?: boolean;
  /** Image and file parts to send with the message. */
  attachmentParts?: MessagePart[];
}

export interface ChatbotContextValue {
  config: ChatbotConfig;
  store: ChatbotStore;
  sendMessage: (text: string, options?: SendMessageOptions) => Promise<void>;
  stopStreaming: () => void;
  respondToToolApproval: (toolId: string, approved: boolean) => Promise<void>;
}

export const ChatbotContext = createContext<ChatbotContextValue | null>(null);

export function useChatbotContext(): ChatbotContextValue {
  const ctx = useContext(ChatbotContext);
  if (!ctx) {
    throw new Error("useChatbotContext must be used within ChatbotProvider");
  }
  return ctx;
}
