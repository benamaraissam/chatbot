import { Sparkles } from "lucide-react";
import { useEffect, useRef } from "react";
import { useChatbot, useChatbotActions } from "../hooks";
import { useChatbotContext } from "../core/context";
import { AssistantTurn } from "./AssistantTurn";
import { MessageBubble } from "./MessageBubble";
import { PendingAssistantTurn } from "./PendingAssistantTurn";

const DEFAULT_SUGGESTIONS = [
  "thinking demo",
  "weather in Tokyo",
  "full demo",
  "send approval email",
  "error demo",
  "markdown demo",
];

export function MessageList() {
  const { config } = useChatbotContext();
  const { sendMessage } = useChatbotActions();
  const messages = useChatbot((s) => s.messages);
  const isStreaming = useChatbot((s) => s.isStreaming);
  const isAwaitingReply = useChatbot((s) => s.isAwaitingReply);
  const streamingMessageId = useChatbot((s) => s.streamingMessageId);
  const streamingText = useChatbot((s) => s.streamingText);
  const error = useChatbot((s) => s.error);
  const bottomRef = useRef<HTMLDivElement>(null);
  const liveRef = useRef<HTMLDivElement>(null);

  const suggestions = config.suggestions ?? DEFAULT_SUGGESTIONS;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText, isAwaitingReply]);

  useEffect(() => {
    if (isStreaming && streamingText && liveRef.current) {
      liveRef.current.textContent = streamingText.slice(-120);
    }
  }, [isStreaming, streamingText]);

  return (
    <div className="cb-flex-1 cb-overflow-y-auto cb-bg-cb-bg cb-px-3 cb-py-3">
      <div ref={liveRef} className="cb-sr-only" aria-live="polite" aria-atomic="true" />

      {messages.length === 0 && (
        <div className="cb-flex cb-h-full cb-min-h-[200px] cb-flex-col cb-items-center cb-justify-center cb-gap-5 cb-py-8">
          <div className="cb-flex cb-h-12 cb-w-12 cb-items-center cb-justify-center cb-rounded-2xl cb-bg-[var(--cb-primary-muted)] cb-text-cb-primary">
            <Sparkles size={22} />
          </div>
          <div className="cb-text-center">
            <p className="cb-text-[15px] cb-font-medium cb-text-cb-text">How can I help?</p>
            <p className="cb-mt-1 cb-text-[12px] cb-text-cb-muted">
              Ask anything — answers stream in real time.
            </p>
          </div>
          <div className="cb-flex cb-w-full cb-max-w-[280px] cb-flex-col cb-gap-1.5">
            {suggestions.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => void sendMessage(prompt)}
                className="cb-rounded-lg cb-border cb-border-cb-border cb-bg-[var(--cb-btn-ghost-bg)] cb-px-3 cb-py-2 cb-text-left cb-text-[12px] cb-text-cb-text-secondary cb-transition-colors hover:cb-border-[var(--cb-border-strong)] hover:cb-bg-[var(--cb-btn-ghost-hover)] hover:cb-text-cb-text"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="cb-flex cb-flex-col cb-gap-3">
        {messages.map((msg) =>
          msg.role === "assistant" ? (
            <AssistantTurn
              key={msg.id}
              message={msg}
              isStreaming={isStreaming && msg.id === streamingMessageId}
              streamingText={
                isStreaming && msg.id === streamingMessageId ? streamingText : undefined
              }
            />
          ) : (
            <MessageBubble key={msg.id} message={msg} />
          ),
        )}
      </div>

      {isAwaitingReply && !streamingMessageId && <PendingAssistantTurn />}

      {error && (
        <p className="cb-mt-2 cb-rounded-lg cb-border cb-border-[var(--cb-error-border)] cb-bg-[var(--cb-error-bg)] cb-px-3 cb-py-2 cb-text-[12px] cb-text-[var(--cb-error-text)]">
          {error}
        </p>
      )}
      <div ref={bottomRef} className="cb-h-1" />
    </div>
  );
}
