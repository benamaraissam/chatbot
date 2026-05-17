import { useChatbot } from "./useChatbot";

/** Streaming state for the active assistant response. */
export function useStreamingChat() {
  const isStreaming = useChatbot((s) => s.isStreaming);
  const streamingText = useChatbot((s) => s.streamingText);
  const streamingMessageId = useChatbot((s) => s.streamingMessageId);
  const error = useChatbot((s) => s.error);

  return { isStreaming, streamingText, streamingMessageId, error };
}
