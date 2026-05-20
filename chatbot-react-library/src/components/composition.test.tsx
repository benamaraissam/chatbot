/**
 * High-coverage composition test: mounts the FloatingChatbot inside a real
 * ChatbotProvider with a mocked fetch backend. Exercises the render paths of
 * FloatingButton, ChatWindow, ChatHeader, MessageList, ChatInput,
 * ComposerAttachments — without needing a real backend.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ChatbotProvider } from "../core/ChatbotProvider";
import { FloatingChatbot } from "./FloatingChatbot";

function mockSSEResponse(): Response {
  const enc = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      const frames = [
        'event: message_start\ndata: {"id":"m_a","role":"assistant"}\n\n',
        'event: text_delta\ndata: {"delta":"Hello "}\n\n',
        'event: text_delta\ndata: {"delta":"world"}\n\n',
        "event: message_end\ndata: {}\n\n",
        "event: done\ndata: {}\n\n",
      ];
      for (const f of frames) controller.enqueue(enc.encode(f));
      controller.close();
    },
  });
  return new Response(body, { status: 200 });
}

describe("composition: FloatingChatbot end-to-end", () => {
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

  it("renders just the FAB when closed", () => {
    render(
      <ChatbotProvider endpoint="/api/chat" theme="light" persist={false}>
        <FloatingChatbot />
      </ChatbotProvider>,
    );
    // FAB is the only visible button initially.
    expect(screen.getByRole("button", { name: /open chat/i })).toBeInTheDocument();
  });

  it("opens the chat window, lets the user type, and sends a message", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(mockSSEResponse()) as unknown as typeof fetch;

    render(
      <ChatbotProvider endpoint="/api/chat" theme="light" persist={false} title="Helper">
        <FloatingChatbot />
      </ChatbotProvider>,
    );

    // Click the FAB to open the panel.
    fireEvent.click(screen.getByRole("button", { name: /open chat/i }));

    // Header reflects the configured title.
    expect(await screen.findByRole("heading", { name: /helper/i })).toBeInTheDocument();

    // Type into the composer and submit.
    const composer = screen.getByPlaceholderText(/message/i) as HTMLTextAreaElement;
    fireEvent.change(composer, { target: { value: "hi" } });
    fireEvent.keyDown(composer, { key: "Enter", code: "Enter" });

    // The assistant text appears once the SSE stream finishes. The text shows
    // up in both the visible <p> and an aria-live announcer; both should match.
    await waitFor(() => {
      const matches = screen.getAllByText(/Hello world/);
      expect(matches.length).toBeGreaterThan(0);
    });

    // The mocked fetch was called exactly once.
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });
});
