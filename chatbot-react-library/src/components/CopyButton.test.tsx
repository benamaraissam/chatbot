import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CopyButton } from "./CopyButton";

describe("<CopyButton />", () => {
  beforeEach(() => {
    // jsdom does not implement the Clipboard API; stub it.
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders an accessible Copy label by default", () => {
    render(<CopyButton text="hello" />);
    const button = screen.getByRole("button", { name: /copy/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("Copy");
  });

  it("copies the configured text to the clipboard on click", () => {
    render(<CopyButton text="hello world" />);
    fireEvent.click(screen.getByRole("button"));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("hello world");
  });

  it("flips to the Copied state after a successful copy", async () => {
    render(<CopyButton text="hi" />);
    fireEvent.click(screen.getByRole("button"));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /copied/i }),
      ).toBeInTheDocument(),
    );
    expect(screen.getByRole("button")).toHaveTextContent("Copied");
  });

  it("is a no-op when the text is empty / whitespace", () => {
    render(<CopyButton text="   " />);
    fireEvent.click(screen.getByRole("button"));
    expect(navigator.clipboard.writeText).not.toHaveBeenCalled();
  });

  it("hides the visible label when showLabel is false", () => {
    render(<CopyButton text="hi" showLabel={false} />);
    const button = screen.getByRole("button", { name: /copy/i });
    // The accessible name comes from aria-label, not visible text.
    expect(button.textContent).not.toContain("Copy");
  });
});
