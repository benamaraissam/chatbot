import { describe, expect, it } from "vitest";
import type { ToolCallState } from "../types";
import {
  formatToolInput,
  formatToolName,
  getToolInputSummary,
  getToolsForMessage,
  hasRunningTools,
} from "./thread";

function tool(partial: Partial<ToolCallState>): ToolCallState {
  return {
    id: partial.id ?? "t_1",
    name: partial.name ?? "do_thing",
    input: partial.input ?? {},
    status: partial.status ?? "running",
    startedAt: partial.startedAt,
    messageId: partial.messageId,
    inputRaw: partial.inputRaw,
    output: partial.output,
    isError: partial.isError,
  };
}

describe("getToolsForMessage", () => {
  it("filters tools by messageId and orders by startedAt", () => {
    const calls: Record<string, ToolCallState> = {
      a: tool({ id: "a", messageId: "m_1", startedAt: 200 }),
      b: tool({ id: "b", messageId: "m_1", startedAt: 100 }),
      c: tool({ id: "c", messageId: "m_2", startedAt: 150 }),
    };
    const tools = getToolsForMessage(calls, "m_1");
    expect(tools.map((t) => t.id)).toEqual(["b", "a"]);
  });

  it("returns an empty array when no tools match", () => {
    expect(getToolsForMessage({}, "m_x")).toEqual([]);
  });
});

describe("formatToolInput", () => {
  it("returns the raw input string when available", () => {
    expect(formatToolInput(tool({ inputRaw: '{"city":"Paris"}' }))).toBe(
      '{"city":"Paris"}',
    );
  });

  it("returns empty string when there is no input at all", () => {
    expect(formatToolInput(tool({ input: {} }))).toBe("");
  });

  it("pretty-prints the parsed input object when no raw is available", () => {
    expect(formatToolInput(tool({ input: { city: "Paris" } }))).toBe(
      JSON.stringify({ city: "Paris" }, null, 2),
    );
  });
});

describe("hasRunningTools", () => {
  it("returns true when any tool is running", () => {
    expect(hasRunningTools([tool({ status: "done" }), tool({ status: "running" })])).toBe(true);
  });

  it("returns false when no tool is running", () => {
    expect(hasRunningTools([tool({ status: "done" }), tool({ status: "error" })])).toBe(false);
  });
});

describe("formatToolName", () => {
  it("turns snake_case into Title Case", () => {
    expect(formatToolName("get_weather")).toBe("Get Weather");
  });

  it("splits camelCase boundaries", () => {
    expect(formatToolName("getWeatherForCity")).toBe("Get Weather For City");
  });
});

describe("getToolInputSummary", () => {
  it("returns null when the input object is empty", () => {
    expect(getToolInputSummary(tool({ input: {} }))).toBeNull();
  });

  it("renders up to three entries separated by middle dots", () => {
    const summary = getToolInputSummary(
      tool({ input: { city: "Paris", units: "metric", days: 5, extra: "ignored" } }),
    );
    expect(summary).toBe("city: Paris · units: metric · days: 5");
  });

  it("prefers parsed inputRaw when present", () => {
    const summary = getToolInputSummary(
      tool({ inputRaw: '{"q":"weather"}' }),
    );
    expect(summary).toBe("q: weather");
  });

  it("returns null when inputRaw is not a JSON object", () => {
    expect(getToolInputSummary(tool({ inputRaw: "not json" }))).toBeNull();
    expect(getToolInputSummary(tool({ inputRaw: "[1,2,3]" }))).toBeNull();
  });
});
