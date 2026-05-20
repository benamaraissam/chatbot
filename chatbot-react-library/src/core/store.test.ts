import { describe, expect, it } from "vitest";
import { createChatbotStore } from "./store";

describe("createChatbotStore", () => {
  it("starts closed with no messages and not streaming", () => {
    const useStore = createChatbotStore();
    const state = useStore.getState();
    expect(state.isOpen).toBe(false);
    expect(state.messages).toEqual([]);
    expect(state.isStreaming).toBe(false);
    expect(state.isAwaitingReply).toBe(false);
  });

  it("assigns a non-empty conversation id", () => {
    const useStore = createChatbotStore();
    const id = useStore.getState().conversationId;
    expect(typeof id).toBe("string");
    expect(id).toMatch(/^conv_/);
  });

  it("toggleOpen flips the open state", () => {
    const useStore = createChatbotStore();
    useStore.getState().toggleOpen();
    expect(useStore.getState().isOpen).toBe(true);
    useStore.getState().toggleOpen();
    expect(useStore.getState().isOpen).toBe(false);
  });

  it("addMessage appends to the messages list", () => {
    const useStore = createChatbotStore();
    useStore.getState().addMessage({
      id: "m_1",
      role: "user",
      parts: [{ type: "text", text: "hi" }],
    } as never);
    expect(useStore.getState().messages).toHaveLength(1);
    expect(useStore.getState().messages[0].id).toBe("m_1");
  });

  it("resetStreaming clears all streaming state", () => {
    const useStore = createChatbotStore();
    useStore.getState().setStreaming(true);
    useStore.getState().setAwaitingReply(true);
    useStore.getState().appendStreamingText("hello");
    useStore.getState().resetStreaming();
    const s = useStore.getState();
    expect(s.isStreaming).toBe(false);
    expect(s.isAwaitingReply).toBe(false);
    expect(s.streamingText).toBe("");
    expect(s.streamingMessageId).toBeNull();
  });

  it("setTheme applies the resolved theme for explicit modes", () => {
    const useStore = createChatbotStore();
    useStore.getState().setTheme("dark");
    expect(useStore.getState().theme).toBe("dark");
    expect(useStore.getState().resolvedTheme).toBe("dark");
  });
});
