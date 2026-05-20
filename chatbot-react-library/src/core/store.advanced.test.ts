import { describe, expect, it } from "vitest";
import { createChatbotStore } from "./store";

describe("createChatbotStore — advanced state transitions", () => {
  it("updateMessage applies an updater function to the matching id only", () => {
    const useStore = createChatbotStore();
    const { addMessage, updateMessage } = useStore.getState();
    addMessage({ id: "m_1", role: "user", parts: [{ type: "text", text: "a" }] } as never);
    addMessage({ id: "m_2", role: "user", parts: [{ type: "text", text: "b" }] } as never);

    updateMessage("m_2", (m) => ({
      ...m,
      parts: [{ type: "text", text: "B!" }],
    }) as never);

    const msgs = useStore.getState().messages;
    expect(msgs[0].parts[0]).toMatchObject({ text: "a" });
    expect(msgs[1].parts[0]).toMatchObject({ text: "B!" });
  });

  it("setConversationId replaces the id", () => {
    const useStore = createChatbotStore();
    useStore.getState().setConversationId("conv_custom");
    expect(useStore.getState().conversationId).toBe("conv_custom");
  });

  it("appendStreamingText and appendThinkingText concatenate deltas", () => {
    const useStore = createChatbotStore();
    useStore.getState().appendStreamingText("Hel");
    useStore.getState().appendStreamingText("lo");
    useStore.getState().appendThinkingText("Thinking ");
    useStore.getState().appendThinkingText("hard");

    const s = useStore.getState();
    expect(s.streamingText).toBe("Hello");
    expect(s.streamingThinkingText).toBe("Thinking hard");
  });

  it("upsertToolCall creates a new entry and then patches it", () => {
    const useStore = createChatbotStore();
    const { upsertToolCall, setStreamingMessageId } = useStore.getState();
    setStreamingMessageId("m_1");

    upsertToolCall("t_1", { name: "get_weather", input: { city: "Paris" } });
    let tc = useStore.getState().toolCalls["t_1"];
    expect(tc.name).toBe("get_weather");
    expect(tc.status).toBe("running");
    expect(tc.messageId).toBe("m_1");

    upsertToolCall("t_1", { status: "done", output: { temp_c: 18 } });
    tc = useStore.getState().toolCalls["t_1"];
    expect(tc.status).toBe("done");
    expect(tc.output).toEqual({ temp_c: 18 });
    // Original input is preserved across upserts.
    expect(tc.input).toEqual({ city: "Paris" });
  });

  it("togglePanelWide flips the wide-panel flag", () => {
    const useStore = createChatbotStore();
    expect(useStore.getState().panelWide).toBe(false);
    useStore.getState().togglePanelWide();
    expect(useStore.getState().panelWide).toBe(true);
  });

  it("toggleEmbeddedPanelCollapsed flips the collapsed flag", () => {
    const useStore = createChatbotStore();
    expect(useStore.getState().embeddedPanelCollapsed).toBe(false);
    useStore.getState().toggleEmbeddedPanelCollapsed();
    expect(useStore.getState().embeddedPanelCollapsed).toBe(true);
  });
});
