/** @type {import('tailwindcss').Config} */
export default {
  prefix: "cb-",
  content: ["./src/**/*.{ts,tsx}"],
  corePlugins: {
    preflight: false,
  },
  theme: {
    extend: {
      colors: {
        cb: {
          bg: "var(--cb-bg)",
          "bg-elevated": "var(--cb-bg-elevated)",
          surface: "var(--cb-surface)",
          border: "var(--cb-border)",
          text: "var(--cb-text)",
          "text-secondary": "var(--cb-text-secondary)",
          muted: "var(--cb-muted)",
          icon: "var(--cb-icon)",
          "icon-muted": "var(--cb-icon-muted)",
          primary: "var(--cb-primary)",
          "primary-fg": "var(--cb-primary-fg)",
        },
      },
      boxShadow: {
        panel: "var(--cb-shadow-panel)",
        fab: "var(--cb-shadow-fab)",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
