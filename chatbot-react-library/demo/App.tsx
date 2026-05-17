import { useState } from "react";
import { ChatbotProvider, ChatWindow, FloatingChatbot } from "../src";
import type { ThemeMode } from "../src/core/types";
import { DemoPage, type DemoDisplayMode } from "./DemoPage";
import "./demo.css";

const ENDPOINT =
  import.meta.env.VITE_CHATBOT_ENDPOINT ?? "/api/chat/chat";

const DEMO_PROMPTS = [
  "thinking demo",
  "What's the weather in Paris?",
  "full demo",
  "send approval email",
  "markdown demo",
];

export function App() {
  const [theme, setTheme] = useState<ThemeMode>("system");
  const [primaryColor, setPrimaryColor] = useState<string | undefined>(undefined);
  const [attachmentsEnabled, setAttachmentsEnabled] = useState(true);
  const [displayMode, setDisplayMode] = useState<DemoDisplayMode>("floating");

  const isEmbedded = displayMode === "embedded";

  return (
    <div className={`demo-app demo-app--${displayMode}`}>
      <DemoPage
        endpoint={ENDPOINT}
        theme={theme}
        onThemeChange={setTheme}
        primaryColor={primaryColor}
        onPrimaryColorChange={setPrimaryColor}
        attachmentsEnabled={attachmentsEnabled}
        onAttachmentsEnabledChange={setAttachmentsEnabled}
        displayMode={displayMode}
        onDisplayModeChange={setDisplayMode}
      />

      <ChatbotProvider
        key={displayMode}
        endpoint={ENDPOINT}
        title="Assistant"
        placeholder="Message…"
        theme={theme}
        primaryColor={primaryColor}
        allowThemeToggle={theme === "system"}
        suggestions={DEMO_PROMPTS}
        attachments={{ enabled: attachmentsEnabled }}
        hostLayout={isEmbedded ? "block" : "overlay"}
      >
        {isEmbedded ? (
          <aside className="demo-chat-sidebar">
            <ChatWindow embedded />
          </aside>
        ) : (
          <FloatingChatbot />
        )}
      </ChatbotProvider>
    </div>
  );
}
