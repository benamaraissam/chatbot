import type { Message } from "../types";
import { IMAGE_ONLY_DEFAULT_PROMPT } from "../utils/attachments";
import { getMessageText, isImageLikePart, isFilePart } from "../utils/messageParts";
import { CopyButton } from "./CopyButton";
import { MarkdownMessage } from "./MarkdownMessage";
import { MessageAttachments } from "./MessageAttachments";
import { StreamingCursor } from "./StreamingCursor";

interface MessageBubbleProps {
  message: Message;
  streamingText?: string;
  isStreaming?: boolean;
  embedded?: boolean;
}

export function MessageBubble({
  message,
  streamingText,
  isStreaming,
  embedded = false,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const text =
    isStreaming && streamingText !== undefined
      ? streamingText
      : getMessageText(message);
  const showMarkdown = !isUser && !isStreaming && text.trim().length > 0;
  const showPlainStream = !isUser && isStreaming;
  const canCopy = !isStreaming && text.trim().length > 0;
  const hasAttachments = message.parts.some(
    (p) => isImageLikePart(p) || isFilePart(p),
  );
  const hasAssistantFiles =
    !isUser && message.parts.some((p) => isFilePart(p));
  const showUserText =
    Boolean(text) && !(text === IMAGE_ONLY_DEFAULT_PROMPT && hasAttachments);

  if (isUser) {
    return (
      <div className="cb-flex cb-flex-col cb-items-end cb-gap-1.5 cb-px-0.5">
        {hasAttachments ? (
          <MessageAttachments parts={message.parts} variant="user" />
        ) : null}
        {showUserText ? (
          <div className="cb-user-bubble cb-max-w-[85%]">
            <p className="cb-whitespace-pre-wrap cb-break-words">{text}</p>
          </div>
        ) : null}
        {canCopy && showUserText ? (
          <CopyButton text={text} ariaLabel="Copy message" className="cb-copy-btn--inline" />
        ) : null}
      </div>
    );
  }

  const assistantContent = (
    <div className={`cb-assistant-message ${embedded ? "cb-w-full" : "cb-max-w-full"}`}>
      <div className="cb-assistant-bubble">
        {showPlainStream ? (
          <p className="cb-whitespace-pre-wrap cb-text-[13px] cb-leading-[1.55] cb-text-cb-text">
            {text}
            <StreamingCursor />
          </p>
        ) : showMarkdown ? (
          <MarkdownMessage content={text} />
        ) : (
          <p className="cb-text-[13px] cb-text-cb-muted">…</p>
        )}
      </div>
      {hasAssistantFiles && !isStreaming && (
        <MessageAttachments parts={message.parts} variant="assistant" />
      )}
      {canCopy && (
        <div className="cb-message-actions">
          <CopyButton text={text} ariaLabel="Copy response" />
        </div>
      )}
    </div>
  );

  if (embedded) return assistantContent;

  return <div className="cb-flex cb-justify-start">{assistantContent}</div>;
}
