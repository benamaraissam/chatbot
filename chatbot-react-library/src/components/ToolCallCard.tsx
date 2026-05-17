import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  CloudSun,
  Loader2,
  Mail,
  Search,
  ShieldAlert,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import type { ToolCallState } from "../types";
import { formatToolInput, formatToolName, getToolInputSummary } from "../utils/thread";
import { useChatbotContext } from "../core/context";

interface ToolCallCardProps {
  tool: ToolCallState;
}

const STATUS_META = {
  running: { label: "Running", Icon: Loader2, spin: true },
  done: { label: "Done", Icon: CheckCircle2, spin: false },
  error: { label: "Failed", Icon: AlertTriangle, spin: false },
  approval: { label: "Review", Icon: ShieldAlert, spin: false },
  denied: { label: "Denied", Icon: AlertTriangle, spin: false },
} as const;

const TOOL_ICONS: Record<string, LucideIcon> = {
  get_weather: CloudSun,
  search_docs: Search,
  send_email: Mail,
  simulate_failure: AlertTriangle,
};

function pickToolIcon(name: string): LucideIcon {
  return TOOL_ICONS[name] ?? Zap;
}

function formatOutput(output: unknown): string {
  if (typeof output === "string") return output;
  return JSON.stringify(output, null, 2);
}

function shouldExpandByStatus(status: ToolCallState["status"]): boolean {
  return status === "approval";
}

export function ToolCallCard({ tool }: ToolCallCardProps) {
  const { config, respondToToolApproval } = useChatbotContext();
  const [open, setOpen] = useState(() => shouldExpandByStatus(tool.status));

  const status = tool.status;

  useEffect(() => {
    if (shouldExpandByStatus(status)) {
      setOpen(true);
    } else {
      setOpen(false);
    }
  }, [status]);

  const meta = STATUS_META[status];
  const ToolIcon = pickToolIcon(tool.name);
  const StatusIcon = meta.Icon;
  const displayName = formatToolName(tool.name);
  const summary = getToolInputSummary(tool);
  const inputText = formatToolInput(tool);

  return (
    <article
      className={`cb-tool-card cb-tool-card--${status}`}
      data-expanded={open ? "true" : "false"}
    >
      <button
        type="button"
        className="cb-tool-card-header"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <div className="cb-tool-card-icon" aria-hidden>
          <ToolIcon size={14} strokeWidth={2.25} />
        </div>
        <div className="cb-tool-card-meta">
          <span className="cb-tool-card-eyebrow">Tool</span>
          <span className="cb-tool-card-name">{displayName}</span>
          {summary && !open && (
            <span className="cb-tool-card-summary">{summary}</span>
          )}
        </div>
        <span className="cb-tool-status-pill">
          <StatusIcon
            size={10}
            strokeWidth={2.5}
            className={meta.spin ? "cb-animate-spin" : undefined}
          />
          {meta.label}
        </span>
        <ChevronRight size={14} className="cb-tool-chevron" aria-hidden />
      </button>

      {open && (
        <div className="cb-tool-card-body">
          <div className="cb-tool-code-block">
            <div className="cb-tool-code-label">
              <span>Parameters</span>
            </div>
            <pre className="cb-tool-code-content">{inputText || "{}"}</pre>
          </div>

          {tool.output !== undefined && (
            <div className="cb-tool-code-block">
              <div className="cb-tool-code-label">
                <span>{tool.isError ? "Error" : "Result"}</span>
              </div>
              <pre
                className={`cb-tool-code-content ${tool.isError ? "cb-tool-code-content--error" : ""}`}
              >
                {formatOutput(tool.output)}
              </pre>
            </div>
          )}

          {status === "approval" && (
            <div className="cb-tool-approval-box">
              <p className="cb-tool-approval-title">Allow this action?</p>
              <p className="cb-tool-approval-desc">
                The assistant wants to run <strong>{displayName}</strong>. Approve only if you
                trust this operation.
              </p>
              <div className="cb-tool-approval-actions">
                <button
                  type="button"
                  className="cb-tool-btn-approve"
                  onClick={() => void respondToToolApproval(tool.id, true)}
                >
                  Approve
                </button>
                <button
                  type="button"
                  className="cb-tool-btn-deny"
                  onClick={() => void respondToToolApproval(tool.id, false)}
                >
                  Deny
                </button>
              </div>
              {!config.onToolApproval && (
                <p className="cb-tool-approval-desc" style={{ marginBottom: 0, marginTop: "0.5rem" }}>
                  Tip: pass <code>onToolApproval</code> on ChatbotProvider to hook approvals.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  );
}
