import "@testing-library/jest-dom/vitest";

// ─────────────────────────────────────────────────────────────────────────────
// jsdom polyfills for browser APIs our source touches at module / mount time.
// Individual tests may override these via vi.stubGlobal / spyOn.
// ─────────────────────────────────────────────────────────────────────────────

if (typeof window !== "undefined" && !window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: (query: string): MediaQueryList => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

// jsdom does not implement URL.createObjectURL / URL.revokeObjectURL.
// Provide minimal stubs so utils/attachmentDisplay.ts can call them.
if (typeof URL !== "undefined") {
  let __seq = 0;
  if (typeof URL.createObjectURL !== "function") {
    (URL as unknown as { createObjectURL: (b: unknown) => string }).createObjectURL =
      () => `blob:test-${++__seq}`;
  }
  if (typeof URL.revokeObjectURL !== "function") {
    (URL as unknown as { revokeObjectURL: (s: string) => void }).revokeObjectURL =
      () => {};
  }
}

// jsdom does not implement Element.prototype.scrollIntoView, but some
// components (MessageList, ThinkingIndicator) call it from effects.
if (typeof Element !== "undefined" && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = function () {};
}
