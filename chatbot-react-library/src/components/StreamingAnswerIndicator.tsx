import { ChevronRight, MessageSquare } from "lucide-react";
import { useEffect, useState } from "react";
import { StreamingCursor } from "./StreamingCursor";

interface StreamingAnswerIndicatorProps {
  text: string;
  isStreaming?: boolean;
}

function answerPreview(text: string, max = 72): string {
  const oneLine = text.replace(/\s+/g, " ").trim();
  if (oneLine.length <= max) return oneLine;
  return `${oneLine.slice(0, max)}…`;
}

/** Shown only while the assistant message is streaming; final answer uses MessageBubble. */
export function StreamingAnswerIndicator({
  text,
  isStreaming = true,
}: StreamingAnswerIndicatorProps) {
  const hasText = text.trim().length > 0;
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (isStreaming) {
      setExpanded(false);
    }
  }, [isStreaming]);

  return (
    <div
      className={`cb-response ${expanded ? "cb-response--expanded" : "cb-response--collapsed"}`}
      role="region"
      aria-label="Response in progress"
    >
      <button
        type="button"
        className="cb-response-header"
        onClick={() => hasText && setExpanded(!expanded)}
        aria-expanded={expanded}
        disabled={!hasText}
      >
        <MessageSquare size={14} className="cb-response-icon" strokeWidth={2.25} />
        <span className="cb-response-label">Response</span>
        {isStreaming && (
          <span className="cb-thinking-dots" aria-hidden>
            <span />
            <span />
            <span />
          </span>
        )}
        {!expanded && hasText && (
          <span className="cb-response-preview">{answerPreview(text)}</span>
        )}
        {hasText && <ChevronRight size={16} className="cb-response-chevron" aria-hidden />}
      </button>
      {expanded && hasText && (
        <div className="cb-response-body" aria-live="polite">
          <p className="cb-response-text">
            {text}
            {isStreaming && <StreamingCursor />}
          </p>
        </div>
      )}
    </div>
  );
}
