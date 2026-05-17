import type { ToolCallState } from "../types";

export function getToolsForMessage(
  toolCalls: Record<string, ToolCallState>,
  messageId: string,
): ToolCallState[] {
  return Object.values(toolCalls)
    .filter((t) => t.messageId === messageId)
    .sort((a, b) => (a.startedAt ?? 0) - (b.startedAt ?? 0));
}

export function formatToolInput(tool: ToolCallState): string {
  if (tool.inputRaw?.trim()) {
    return tool.inputRaw;
  }
  const keys = Object.keys(tool.input);
  if (keys.length === 0) return "";
  return JSON.stringify(tool.input, null, 2);
}

export function hasRunningTools(tools: ToolCallState[]): boolean {
  return tools.some((t) => t.status === "running");
}

/** `get_weather` → `Get weather` */
export function formatToolName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** One-line preview for collapsed tool cards */
export function getToolInputSummary(tool: ToolCallState): string | null {
  const input = tool.inputRaw?.trim()
    ? tryParseJson(tool.inputRaw)
    : tool.input;
  if (!input || typeof input !== "object") return null;
  const entries = Object.entries(input as Record<string, unknown>).slice(0, 3);
  if (entries.length === 0) return null;
  return entries
    .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join(" · ");
}

function tryParseJson(raw: string): Record<string, unknown> | null {
  try {
    const v = JSON.parse(raw) as unknown;
    return v && typeof v === "object" && !Array.isArray(v)
      ? (v as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}
