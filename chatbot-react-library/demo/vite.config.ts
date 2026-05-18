import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Resolve directory of this config file without depending on @types/node —
// URL is provided by the DOM lib and import.meta.url is standard ESM,
// so no Node typings are required for the typecheck.
const here = new URL(".", import.meta.url).pathname;

export default defineConfig({
  root: here,
  plugins: [react()],
  resolve: {
    alias: {
      "chatbot-react": new URL("../src/index.ts", import.meta.url).pathname,
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
