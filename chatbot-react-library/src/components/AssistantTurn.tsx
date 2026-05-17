import type { Message } from "../types";
import { getMessageText } from "../utils/messageParts";
import { getToolsForMessage } from "../utils/thread";
import { useChatbot } from "../hooks";
import { BotAvatar } from "./BotAvatar";
import { MessageBubble } from "./MessageBubble";
import { StreamingAnswerIndicator } from "./StreamingAnswerIndicator";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { ToolCallCard } from "./ToolCallCard";

interface AssistantTurnProps {
  message: Message;
  isStreaming: boolean;
  streamingText?: string;
}

export function AssistantTurn({ message, isStreaming, streamingText }: AssistantTurnProps) {
  const toolCalls = useChatbot((s) => s.toolCalls);
  const streamingThinkingText = useChatbot((s) => s.streamingThinkingText);
  const streamingMessageId = useChatbot((s) => s.streamingMessageId);
  const isActiveMessage = isStreaming && message.id === streamingMessageId;

  const tools = getToolsForMessage(toolCalls, message.id);
  const finalizedText = getMessageText(message);
  const streamingAnswerText =
    isActiveMessage && streamingText !== undefined ? streamingText : "";
  const bufferedAnswer = streamingAnswerText.trim();
  const showAnswer = !isActiveMessage && Boolean(finalizedText.trim());

  const thinkingText = isActiveMessage
    ? streamingThinkingText || message.thinking || ""
    : message.thinking || "";

  const isThinkingLive =
    isActiveMessage && !bufferedAnswer && Boolean(streamingThinkingText);
  const showStreamingAnswer = isActiveMessage && !isThinkingLive;
  const showThinkingTrace = Boolean(thinkingText.trim()) || isThinkingLive;
  const showAvatarLoading =
    isActiveMessage &&
    !thinkingText.trim() &&
    !bufferedAnswer &&
    tools.length === 0;
  const showTools = tools.length > 0;

  return (
    <div className="cb-assistant-turn">
      <BotAvatar loading={showAvatarLoading} className="cb-assistant-turn-avatar" />
      <div className="cb-assistant-turn-body">
        {showThinkingTrace && (
          <ThinkingIndicator text={thinkingText} isStreaming={isThinkingLive} />
        )}
        {showStreamingAnswer && (
          <StreamingAnswerIndicator text={streamingAnswerText} isStreaming />
        )}
        {showTools && (
          <div className="cb-tool-stack">
            {tools.map((tool) => (
              <ToolCallCard key={tool.id} tool={tool} />
            ))}
          </div>
        )}
        {showAnswer && (
          <MessageBubble message={message} isStreaming={false} embedded />
        )}
      </div>
    </div>
  );
}
