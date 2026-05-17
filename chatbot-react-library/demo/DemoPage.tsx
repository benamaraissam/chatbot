import type { ThemeMode } from "../src/core/types";

const THEMES: { value: ThemeMode; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
];

const PRIMARY_COLORS: {
  label: string;
  value: string | undefined;
  swatch?: string;
}[] = [
  { label: "Default", value: undefined },
  { label: "Violet", value: "#7c3aed", swatch: "#7c3aed" },
  { label: "Blue", value: "#2563eb", swatch: "#2563eb" },
  { label: "Teal", value: "#0d9488", swatch: "#0d9488" },
  { label: "Rose", value: "#e11d48", swatch: "#e11d48" },
];

const DEMO_PROMPTS = [
  "thinking demo",
  "What's the weather in Paris?",
  "full demo",
  "send approval email",
  "markdown demo",
];

export type DemoDisplayMode = "floating" | "embedded";

export interface DemoPageProps {
  endpoint: string;
  theme: ThemeMode;
  onThemeChange: (theme: ThemeMode) => void;
  primaryColor: string | undefined;
  onPrimaryColorChange: (color: string | undefined) => void;
  attachmentsEnabled: boolean;
  onAttachmentsEnabledChange: (enabled: boolean) => void;
  displayMode: DemoDisplayMode;
  onDisplayModeChange: (mode: DemoDisplayMode) => void;
}

export function DemoPage({
  endpoint,
  theme,
  onThemeChange,
  primaryColor,
  onPrimaryColorChange,
  attachmentsEnabled,
  onAttachmentsEnabledChange,
  displayMode,
  onDisplayModeChange,
}: DemoPageProps) {
  const demoThemeAttr = theme === "light" ? "light" : undefined;
  const isFloating = displayMode === "floating";

  return (
    <div className="demo-page" data-cb-theme={demoThemeAttr}>
      <div className="demo-bg" aria-hidden>
        <div className="demo-grid" />
      </div>

      <main className="demo-shell">
        <span className="demo-badge">React + FastAPI</span>
        <h1 className="demo-title">Chatbot component demo</h1>
        <p className="demo-lead">
          Configure the chat below. Switch display mode to try floating or sidebar
          integration — this page stays in place.
        </p>

        <div className="demo-stack">
          <section className="demo-card">
            <h2 className="demo-card-title">Integration</h2>

            <div className="demo-field">
              <span className="demo-field-label">Display mode</span>
              <div className="demo-segment" role="group" aria-label="Chat display mode">
                <button
                  type="button"
                  className={`demo-segment-btn ${isFloating ? "demo-segment-btn--active" : ""}`}
                  onClick={() => onDisplayModeChange("floating")}
                >
                  Floating
                </button>
                <button
                  type="button"
                  className={`demo-segment-btn ${!isFloating ? "demo-segment-btn--active" : ""}`}
                  onClick={() => onDisplayModeChange("embedded")}
                >
                  Sidebar
                </button>
              </div>
              <p className="demo-field-hint">
                {isFloating
                  ? "FloatingChatbot · hostLayout=\"overlay\""
                  : "ChatWindow embedded · hostLayout=\"block\""}
              </p>
            </div>
          </section>

          <section className="demo-card">
            <h2 className="demo-card-title">Appearance</h2>

            <div className="demo-field">
              <span className="demo-field-label">File attachments</span>
              <div className="demo-segment" role="group" aria-label="File attachments">
                <button
                  type="button"
                  className={`demo-segment-btn ${attachmentsEnabled ? "demo-segment-btn--active" : ""}`}
                  onClick={() => onAttachmentsEnabledChange(true)}
                >
                  Enabled
                </button>
                <button
                  type="button"
                  className={`demo-segment-btn ${!attachmentsEnabled ? "demo-segment-btn--active" : ""}`}
                  onClick={() => onAttachmentsEnabledChange(false)}
                >
                  Disabled
                </button>
              </div>
            </div>

            <div className="demo-field">
              <span className="demo-field-label">Theme</span>
              <div className="demo-segment" role="group" aria-label="Chat theme">
                {THEMES.map(({ value, label }) => (
                  <button
                    key={value}
                    type="button"
                    className={`demo-segment-btn ${theme === value ? "demo-segment-btn--active" : ""}`}
                    onClick={() => onThemeChange(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="demo-field">
              <span className="demo-field-label">Primary color</span>
              <div className="demo-colors">
                {PRIMARY_COLORS.map(({ label, value, swatch }) => (
                  <button
                    key={label}
                    type="button"
                    className={`demo-color-btn ${primaryColor === value ? "demo-color-btn--active" : ""}`}
                    onClick={() => onPrimaryColorChange(value)}
                  >
                    <span
                      className={`demo-swatch ${!swatch ? "demo-swatch--default" : ""}`}
                      style={swatch ? { background: swatch } : undefined}
                      aria-hidden
                    />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className="demo-card">
            <h2 className="demo-card-title">Sample prompts</h2>
            <div className="demo-prompts">
              {DEMO_PROMPTS.map((text) => (
                <span key={text} className="demo-prompt">
                  {text}
                </span>
              ))}
            </div>
            <p className="demo-code">
              <strong>Backend:</strong> {endpoint}
              <br />
              <strong>Run:</strong> cd ../chatbot-python-library && python
              examples/02_fastapi_app.py
            </p>
          </section>

          <p className="demo-footer">
            Floating: button bottom-right ↘ · Sidebar: panel docked on the right →
          </p>
        </div>
      </main>
    </div>
  );
}
