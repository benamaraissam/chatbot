/**
 * Composition test that exercises the tool-call render path: ToolCallCard,
 * AssistantTurn, and the streaming-end → final-bubble transition.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ChatbotProvider } from "../core/ChatbotProvider";
import { FloatingChatbot } from "./FloatingChatbot";

function mockSSEWithToolCall(): Response {
  const enc = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      const frames = [
        'event: message_start\ndata: {"id":"m_a","role":"assistant"}\n\n',
        'event: tool_call_start\ndata: {"id":"t_1","name":"get_weather","input":{"city":"Paris"}}\n\n',
        'event: tool_result\ndata: {"id":"t_1","output":{"temp_c":22}}\n\n',
        'event: tool_call_end\ndata: {"id":"t_1"}\n\n',
        'event: text_delta\ndata: {"delta":"It is 22°C in Paris."}\n\n',
        "event: message_end\ndata: {}\n\n",
        "event: done\ndata: {}\n\n",
      ];
      for (const f of frames) controller.enqueue(enc.encode(f));
      controller.close();
    },
  });
  return new Response(body, { status: 200 });
}

describe("composition with tool calls", () => {
  let original: typeof fetch;
  beforeEach(() => {
    localStorage.clear();
    original = globalThis.fetch;
  });
  afterEach(() => {
    globalThis.fetch = original;
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders a tool-call card alongside the assistant turn", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(mockSSEWithToolCall()) as unknown as typeof fetch;

    render(
      <ChatbotProvider
        endpoint="/api/chat"
        theme="light"
        persist={false}
        title="Assistant"
      >
        <FloatingChatbot />
      </ChatbotProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /open chat/i }));
    const composer = screen.getByPlaceholderText(/message/i);
    fireEvent.change(composer, { target: { value: "weather in Paris" } });
    fireEvent.keyDown(composer, { key: "Enter", code: "Enter" });

    // Tool-call card surfaces the tool name (formatToolName turns
    // "get_weather" into "Get Weather").
    await waitFor(() =>
      expect(
        screen.getAllByText(/Get Weather/i).length,
      ).toBeGreaterThan(0),
    );

    // Final assistant text lands too.
    await waitFor(() =>
      expect(
        screen.getAllByText(/22°C in Paris/i).length,
      ).toBeGreaterThan(0),
    );
  });
});
