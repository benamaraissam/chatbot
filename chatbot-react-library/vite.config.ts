import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import dts from "vite-plugin-dts";

export default defineConfig({
  plugins: [
    react(),
    dts({
      include: ["src"],
      rollupTypes: true,
      tsconfigPath: "./tsconfig.build.json",
    }),
  ],
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.ts"),
      name: "ChatbotReact",
      formats: ["es", "umd"],
      fileName: (format) => (format === "es" ? "chatbot-react.js" : "chatbot-react.umd.cjs"),
    },
    rollupOptions: {
      external: ["react", "react-dom", "react/jsx-runtime", "shiki"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          "react/jsx-runtime": "jsxRuntime",
        },
        assetFileNames: "chatbot-react.[ext]",
      },
    },
    cssCodeSplit: false,
    sourcemap: true,
  },
});
