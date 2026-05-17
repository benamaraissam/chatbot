import { Bot } from "lucide-react";

interface BotAvatarProps {
  /** Pulsing dots beside the icon while waiting for the model. */
  loading?: boolean;
  className?: string;
}

export function BotAvatar({ loading = false, className = "" }: BotAvatarProps) {
  return (
    <div
      className={`cb-bot-avatar-wrap ${className}`.trim()}
      aria-hidden={!loading}
    >
      <div className="cb-bot-avatar">
        <Bot size={15} strokeWidth={2.25} />
      </div>
      {loading && (
        <span className="cb-bot-loading" role="status" aria-label="Loading response">
          <span className="cb-bot-loading-dots" aria-hidden>
            <span />
            <span />
            <span />
          </span>
        </span>
      )}
    </div>
  );
}
