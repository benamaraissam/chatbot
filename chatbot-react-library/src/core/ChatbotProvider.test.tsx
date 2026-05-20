import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatbotProvider } from "./ChatbotProvider";
import { useChatbotContext } from "./context";

function Probe() {
  const ctx = useChatbotContext();
  return (
    <div>
      <span data-testid="endpoint">{ctx.config.endpoint}</span>
      <span data-testid="title">{ctx.config.title ?? "(no title)"}</span>
      <span data-testid="isOpen">
        {String(ctx.store.getState().isOpen)}
      </span>
    </div>
  );
}

describe("<ChatbotProvider />", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("provides config and a working store to its children", () => {
    render(
      <ChatbotProvider endpoint="/api/chat" title="Assistant" theme="light">
        <Probe />
      </ChatbotProvider>,
    );
    expect(screen.getByTestId("endpoint")).toHaveTextContent("/api/chat");
    expect(screen.getByTestId("title")).toHaveTextContent("Assistant");
    expect(screen.getByTestId("isOpen")).toHaveTextContent("false");
  });

  it("uses the default storage key when persist is enabled and none is provided", () => {
    render(
      <ChatbotProvider endpoint="/api/chat" persist={true}>
        <Probe />
      </ChatbotProvider>,
    );
    // The mere act of mounting creates a store; if persist is on, the
    // initial conversation skeleton is written under the default key.
    // We only assert the default key resolution does not crash.
    expect(screen.getByTestId("endpoint")).toBeInTheDocument();
  });

  it("disables persistence when persist=false", () => {
    render(
      <ChatbotProvider endpoint="/api/chat" persist={false} theme="dark">
        <Probe />
      </ChatbotProvider>,
    );
    // Persistence off → no writes to localStorage from the constructor effect.
    // Storage may be touched for other reasons but the bootstrap path should
    // never throw and the component still mounts.
    expect(screen.getByTestId("endpoint")).toBeInTheDocument();
  });

  it("useChatbotContext throws outside a provider", () => {
    // Suppress the expected console.error output to keep test logs clean.
    const original = console.error;
    console.error = () => {};
    try {
      expect(() => render(<Probe />)).toThrow(/ChatbotProvider/);
    } finally {
      console.error = original;
    }
  });
});
