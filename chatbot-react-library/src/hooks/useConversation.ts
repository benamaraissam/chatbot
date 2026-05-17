import { useChatbot } from "./useChatbot";

export function useConversation() {
  const messages = useChatbot((s) => s.messages);
  const conversationId = useChatbot((s) => s.conversationId);
  const toolCalls = useChatbot((s) => s.toolCalls);

  return { messages, conversationId, toolCalls };
}
