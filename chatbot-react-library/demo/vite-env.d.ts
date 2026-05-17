/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CHATBOT_ENDPOINT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
