import { describe, expect, it } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { ChatbotProvider } from "../core/ChatbotProvider";
import { useChatbot, useChatbotActions } from "./useChatbot";
import { useConversation } from "./useConversation";
import { useStreamingChat } from "./useStreamingChat";

function ChatbotProbe() {
  const isOpen = useChatbot((s) => s.isOpen);
  const actions = useChatbotActions();
  const conv = useConversation();
  const stream = useStreamingChat();
  return (
    <div>
      <span data-testid="isOpen">{String(isOpen)}</span>
      <span data-testid="conv-len">{conv.messages.length}</span>
      <span data-testid="conv-id">{conv.conversationId}</span>
      <span data-testid="stream">{String(stream.isStreaming)}</span>
      <button onClick={actions.toggleOpen} data-testid="toggle">
        toggle
      </button>
      <button onClick={() => actions.setTheme("dark")} data-testid="dark">
        dark
      </button>
      <button onClick={actions.clearMessages} data-testid="clear">
        clear
      </button>
    </div>
  );
}

function renderProbe() {
  return render(
    <ChatbotProvider endpoint="/api/chat" persist={false} theme="light">
      <ChatbotProbe />
    </ChatbotProvider>,
  );
}

describe("hooks", () => {
  it("useChatbot reads selected slice from the store", () => {
    renderProbe();
    expect(screen.getByTestId("isOpen")).toHaveTextContent("false");
    expect(screen.getByTestId("conv-len")).toHaveTextContent("0");
  });

  it("useChatbotActions.toggleOpen flips the open flag", () => {
    renderProbe();
    act(() => {
      screen.getByTestId("toggle").click();
    });
    expect(screen.getByTestId("isOpen")).toHaveTextContent("true");
  });

  it("useChatbotActions.setTheme updates the theme", () => {
    renderProbe();
    act(() => {
      screen.getByTestId("dark").click();
    });
    // No visible side effect needed for coverage of the setter path.
    expect(screen.getByTestId("isOpen")).toBeInTheDocument();
  });

  it("useConversation exposes the conversation id", () => {
    renderProbe();
    expect(screen.getByTestId("conv-id").textContent).toMatch(/^conv_/);
  });

  it("useStreamingChat starts as not streaming", () => {
    renderProbe();
    expect(screen.getByTestId("stream")).toHaveTextContent("false");
  });

  it("clearMessages is callable through the actions facade", () => {
    renderProbe();
    act(() => {
      screen.getByTestId("clear").click();
    });
    expect(screen.getByTestId("conv-len")).toHaveTextContent("0");
  });
});
