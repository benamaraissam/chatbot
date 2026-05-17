import { Bot, Moon, Sun, Trash2, X } from "lucide-react";
import { useChatbot, useChatbotActions } from "../hooks";
import { useChatbotContext } from "../core/context";

interface ChatHeaderProps {
  /** Docked sidebar: no close control (collapse uses the panel edge toggle). */
  embedded?: boolean;
}

export function ChatHeader({ embedded = false }: ChatHeaderProps) {
  const { config } = useChatbotContext();
  const title = config.title ?? "Assistant";
  const { setOpen, clearMessages, setTheme } = useChatbotActions();
  const resolvedTheme = useChatbot((s) => s.resolvedTheme);
  const showThemeToggle = config.allowThemeToggle === true;

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  return (
    <header className="cb-header">
      <div className="cb-header-avatar" aria-hidden>
        <Bot size={18} strokeWidth={2.25} />
      </div>

      <div className="cb-header-text">
        <h2 className="cb-header-title cb-truncate">{title}</h2>
        <p className="cb-header-subtitle">
          <span className="cb-header-status-dot" aria-hidden />
          <span>Online · Ready to chat</span>
        </p>
      </div>

      <div className="cb-header-toolbar" role="toolbar" aria-label="Chat actions">
        {showThemeToggle && (
          <button
            type="button"
            onClick={toggleTheme}
            className="cb-btn-ghost"
            title={resolvedTheme === "dark" ? "Light mode" : "Dark mode"}
            aria-label={resolvedTheme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {resolvedTheme === "dark" ? (
              <Sun size={17} strokeWidth={2} />
            ) : (
              <Moon size={17} strokeWidth={2} />
            )}
          </button>
        )}
        <button
          type="button"
          onClick={clearMessages}
          className="cb-btn-ghost cb-btn-ghost-danger"
          title="Clear conversation"
          aria-label="Clear chat"
        >
          <Trash2 size={17} strokeWidth={2} />
        </button>
        {!embedded && (
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="cb-btn-ghost cb-btn-ghost-close"
            title="Close"
            aria-label="Close chat"
          >
            <X size={17} strokeWidth={2} />
          </button>
        )}
      </div>
    </header>
  );
}
