/**
 * Smoke tests for the simple presentational components — render and assert
 * the visible structure. Designed to lift coverage on components that don't
 * need a full ChatbotProvider context.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BotAvatar } from "./BotAvatar";
import { PendingAssistantTurn } from "./PendingAssistantTurn";
import { StreamingCursor } from "./StreamingCursor";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { StreamingAnswerIndicator } from "./StreamingAnswerIndicator";
import { MarkdownMessage } from "./MarkdownMessage";

describe("<BotAvatar />", () => {
  it("renders the bot icon wrapper", () => {
    const { container } = render(<BotAvatar />);
    expect(container.querySelector(".cb-bot-avatar")).not.toBeNull();
    // loading is false → no role=status pulse.
    expect(container.querySelector('[role="status"]')).toBeNull();
  });

  it("renders the loading indicator when loading", () => {
    render(<BotAvatar loading />);
    expect(screen.getByRole("status", { name: /loading response/i })).toBeInTheDocument();
  });
});

describe("<StreamingCursor />", () => {
  it("renders a hidden caret element", () => {
    const { container } = render(<StreamingCursor />);
    const span = container.querySelector("span");
    expect(span).not.toBeNull();
    // React renders aria-hidden as the string "true" for JSX boolean attrs.
    expect(span!.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("<PendingAssistantTurn />", () => {
  it("renders an avatar in a loading state", () => {
    const { container } = render(<PendingAssistantTurn />);
    expect(container.querySelector(".cb-assistant-turn")).not.toBeNull();
    expect(container.querySelector(".cb-bot-avatar-wrap")).not.toBeNull();
  });
});

describe("<ThinkingIndicator />", () => {
  it("renders nothing when there is no text and not streaming", () => {
    const { container } = render(<ThinkingIndicator text="" isStreaming={false} />);
    // When neither hasText nor isStreaming the parent region is skipped.
    expect(container.querySelector(".cb-thinking")).toBeNull();
  });

  it("renders a region with the Thinking label while streaming", () => {
    render(<ThinkingIndicator text="Considering options..." isStreaming />);
    expect(screen.getByText(/thinking/i)).toBeInTheDocument();
  });
});

describe("<StreamingAnswerIndicator />", () => {
  it("renders an accessible region while streaming", () => {
    render(<StreamingAnswerIndicator text="Computing..." isStreaming />);
    expect(
      screen.getByRole("region", { name: /response in progress/i }),
    ).toBeInTheDocument();
  });
});

describe("<MarkdownMessage />", () => {
  it("renders markdown content as HTML", () => {
    const { container } = render(
      <MarkdownMessage content="**bold** and *italic*" />,
    );
    // remark-gfm + react-markdown produce real <strong>/<em> nodes.
    expect(container.querySelector("strong")).not.toBeNull();
    expect(container.querySelector("em")).not.toBeNull();
  });

  it("renders plain text without crashing", () => {
    const { container } = render(<MarkdownMessage content="just words" />);
    // Text is wrapped in a <p>, so use a text-matcher tolerant of that.
    expect(container.textContent).toContain("just words");
  });
});
