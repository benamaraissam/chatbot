import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatbotProvider } from "../core/ChatbotProvider";
import { ToolCallCard } from "./ToolCallCard";
import type { ToolCallState } from "../types";

function tool(partial: Partial<ToolCallState>): ToolCallState {
  return {
    id: partial.id ?? "t_1",
    name: partial.name ?? "get_weather",
    input: partial.input ?? { city: "Paris" },
    status: partial.status ?? "running",
    startedAt: partial.startedAt ?? Date.now(),
    output: partial.output,
    isError: partial.isError,
    messageId: partial.messageId,
    inputRaw: partial.inputRaw,
  };
}

function renderWithProvider(child: React.ReactNode) {
  return render(
    <ChatbotProvider endpoint="/api/chat" persist={false} theme="light">
      {child}
    </ChatbotProvider>,
  );
}

describe("<ToolCallCard />", () => {
  it("renders the formatted tool name when running", () => {
    renderWithProvider(<ToolCallCard tool={tool({ status: "running" })} />);
    // formatToolName turns "get_weather" into "Get Weather".
    expect(screen.getAllByText(/Get Weather/i).length).toBeGreaterThan(0);
  });

  it("renders the Done state when the call has completed", () => {
    renderWithProvider(
      <ToolCallCard
        tool={tool({ status: "done", output: { temp_c: 22 } })}
      />,
    );
    expect(screen.getByText(/done/i)).toBeInTheDocument();
  });

  it("renders the Failed state for error status", () => {
    renderWithProvider(
      <ToolCallCard
        tool={tool({ status: "error", isError: true, output: "boom" })}
      />,
    );
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
  });

  it("renders the Review state for tool approval requests", () => {
    renderWithProvider(
      <ToolCallCard tool={tool({ status: "approval" })} />,
    );
    expect(screen.getByText(/review/i)).toBeInTheDocument();
  });
});
