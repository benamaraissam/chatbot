import { BotAvatar } from "./BotAvatar";

/** Shown after send, before the first `message_start` SSE event. */
export function PendingAssistantTurn() {
  return (
    <div className="cb-assistant-turn">
      <BotAvatar loading className="cb-assistant-turn-avatar" />
    </div>
  );
}
