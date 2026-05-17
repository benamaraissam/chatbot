import { useChatbotContext } from "../core/context";
import type { ChatbotStore } from "../core/store";

export function useChatbot<T>(selector: (state: ReturnType<ChatbotStore["getState"]>) => T): T {
  const { store } = useChatbotContext();
  return store(selector);
}

export function useChatbotActions() {
  const { sendMessage, stopStreaming, store } = useChatbotContext();
  const setOpen = store((s) => s.setOpen);
  const toggleOpen = store((s) => s.toggleOpen);
  const clearMessages = store((s) => s.clearMessages);
  const setTheme = store((s) => s.setTheme);
  const togglePanelWide = store((s) => s.togglePanelWide);
  const setEmbeddedPanelCollapsed = store((s) => s.setEmbeddedPanelCollapsed);
  const toggleEmbeddedPanelCollapsed = store((s) => s.toggleEmbeddedPanelCollapsed);

  return {
    sendMessage,
    stopStreaming,
    setOpen,
    toggleOpen,
    clearMessages,
    setTheme,
    togglePanelWide,
    setEmbeddedPanelCollapsed,
    toggleEmbeddedPanelCollapsed,
  };
}
