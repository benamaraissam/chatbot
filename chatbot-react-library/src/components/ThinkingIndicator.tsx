import { Brain, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { StreamingCursor } from "./StreamingCursor";

interface ThinkingIndicatorProps {
  text: string;
  isStreaming?: boolean;
}

function thinkingPreview(text: string, max = 72): string {
  const oneLine = text.replace(/\s+/g, " ").trim();
  if (oneLine.length <= max) return oneLine;
  return `${oneLine.slice(0, max)}…`;
}

export function ThinkingIndicator({ text, isStreaming = false }: ThinkingIndicatorProps) {
  const hasText = text.trim().length > 0;
  const [expanded, setExpanded] = useState(isStreaming);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isStreaming && hasText) {
      setExpanded(false);
    }
  }, [isStreaming, hasText]);

  useEffect(() => {
    if (isStreaming) {
      setExpanded(true);
    }
  }, [isStreaming]);

  useEffect(() => {
    if (!isStreaming || !expanded) return;
    const el = bodyRef.current;
    if (!el) return;
    requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight;
    });
  }, [text, isStreaming, expanded]);

  if (!hasText && !isStreaming) {
    return null;
  }

  return (
    <div
      className={`cb-thinking ${expanded ? "cb-thinking--expanded" : "cb-thinking--collapsed"}`}
      role="region"
      aria-label="Reasoning trace"
    >
      <button
        type="button"
        className="cb-thinking-header"
        onClick={() => hasText && setExpanded(!expanded)}
        aria-expanded={expanded}
        disabled={!hasText}
      >
        <Brain size={14} className="cb-thinking-icon" strokeWidth={2.25} />
        <span className="cb-thinking-label">Thinking</span>
        {isStreaming && !hasText && (
          <span className="cb-thinking-dots" aria-hidden>
            <span />
            <span />
            <span />
          </span>
        )}
        {!expanded && hasText && (
          <span className="cb-thinking-preview">{thinkingPreview(text)}</span>
        )}
        {hasText && (
          <ChevronRight size={16} className="cb-thinking-chevron" aria-hidden />
        )}
      </button>
      {expanded && (
        <div
          ref={bodyRef}
          className="cb-thinking-body"
          aria-live={isStreaming ? "polite" : "off"}
        >
          {hasText ? (
            <p className="cb-thinking-text">
              {text}
              {isStreaming && <StreamingCursor />}
            </p>
          ) : (
            <p className="cb-thinking-text cb-thinking-text--placeholder">Reasoning…</p>
          )}
        </div>
      )}
    </div>
  );
}
