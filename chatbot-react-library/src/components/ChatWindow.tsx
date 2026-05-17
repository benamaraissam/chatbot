import { AnimatePresence, motion } from "framer-motion";
import { ChevronsLeft, ChevronsRight } from "lucide-react";
import { useEffect } from "react";
import { useChatbot, useChatbotActions } from "../hooks";
import { ChatHeader } from "./ChatHeader";
import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";

interface ChatWindowProps {
  /** Always-visible panel for sidebars / full-page chat (not floating FAB flow). */
  embedded?: boolean;
  /** Allow collapsing embedded panel to a side rail (default: true when embedded). */
  collapsible?: boolean;
}

type PanelEdgeToggleProps =
  | {
      mode: "wide";
      expanded: boolean;
      onToggle: () => void;
    }
  | {
      mode: "collapse";
      collapsed: boolean;
      onToggle: () => void;
    };

function PanelEdgeToggle(props: PanelEdgeToggleProps) {
  const { mode, onToggle } = props;
  const pressed = mode === "wide" ? props.expanded : props.collapsed;

  const title =
    mode === "wide"
      ? props.expanded
        ? "Narrow panel"
        : "Wide panel"
      : props.collapsed
        ? "Expand sidebar"
        : "Collapse sidebar";

  const ariaLabel =
    mode === "wide"
      ? props.expanded
        ? "Use default chat width"
        : "Use wide chat width"
      : props.collapsed
        ? "Expand chat sidebar"
        : "Collapse chat sidebar";

  const Icon =
    mode === "collapse"
      ? props.collapsed
        ? ChevronsLeft
        : ChevronsRight
      : props.expanded
        ? ChevronsRight
        : ChevronsLeft;

  const isCollapsedPin = mode === "collapse" && props.collapsed;

  return (
    <button
      type="button"
      className={`cb-panel-width-toggle${isCollapsedPin ? " cb-panel-width-toggle--collapsed-pin" : ""}`}
      onClick={onToggle}
      title={title}
      aria-label={ariaLabel}
      aria-pressed={pressed}
    >
      <span className="cb-panel-width-toggle-icon">
        <Icon size={isCollapsedPin ? 22 : 18} strokeWidth={2.5} />
      </span>
    </button>
  );
}

function ChatPanel({
  panelWide,
  embedded = false,
}: {
  panelWide: boolean;
  embedded?: boolean;
}) {
  return (
    <div className={`cb-chat-frame${!embedded && panelWide ? " cb-chat-frame--wide" : ""}`}>
      <motion.div role="dialog" aria-label="Chat" className="cb-chat-panel">
        <ChatHeader embedded={embedded} />
        <MessageList />
        <ChatInput />
      </motion.div>
    </div>
  );
}

function FloatingChatPanel({
  panelWide,
  edgeToggle,
}: {
  panelWide: boolean;
  edgeToggle: Extract<PanelEdgeToggleProps, { mode: "wide" }>;
}) {
  return (
    <div className={`cb-chat-frame${panelWide ? " cb-chat-frame--wide" : ""}`}>
      <PanelEdgeToggle {...edgeToggle} />
      <motion.div role="dialog" aria-label="Chat" className="cb-chat-panel">
        <ChatHeader />
        <MessageList />
        <ChatInput />
      </motion.div>
    </div>
  );
}

export function ChatWindow({ embedded = false, collapsible }: ChatWindowProps) {
  const isOpen = useChatbot((s) => s.isOpen);
  const panelWide = useChatbot((s) => s.panelWide);
  const collapsed = useChatbot((s) => s.embeddedPanelCollapsed);
  const { setOpen, togglePanelWide, toggleEmbeddedPanelCollapsed, setEmbeddedPanelCollapsed } =
    useChatbotActions();

  const canCollapse = embedded && (collapsible ?? true);

  useEffect(() => {
    if (embedded) setEmbeddedPanelCollapsed(false);
  }, [embedded, setEmbeddedPanelCollapsed]);

  if (embedded) {
    const edgeToggle: Extract<PanelEdgeToggleProps, { mode: "collapse" }> | null = canCollapse
      ? {
          mode: "collapse",
          collapsed,
          onToggle: toggleEmbeddedPanelCollapsed,
        }
      : null;

    return (
      <div
        className={`cb-chat-shell cb-chat-shell--embedded${
          collapsed ? " cb-chat-shell--collapsed" : ""
        }`}
      >
        {edgeToggle ? <PanelEdgeToggle {...edgeToggle} /> : null}
        {!collapsed ? <ChatPanel panelWide={false} embedded /> : null}
      </div>
    );
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="cb-fixed cb-inset-0 cb-z-[9998] md:cb-bg-[var(--cb-backdrop)]"
            aria-hidden
            onClick={() => setOpen(false)}
          />
          <motion.div
            key="shell"
            role="presentation"
            initial={{ opacity: 0, y: 20, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 34 }}
            className="cb-chat-shell"
          >
            <FloatingChatPanel
              panelWide={panelWide}
              edgeToggle={{
                mode: "wide",
                expanded: panelWide,
                onToggle: togglePanelWide,
              }}
            />
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
