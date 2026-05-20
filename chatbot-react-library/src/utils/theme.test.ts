import { afterEach, describe, expect, it, vi } from "vitest";
import { resolveTheme } from "./theme";

describe("resolveTheme", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the explicit mode for light", () => {
    expect(resolveTheme("light")).toBe("light");
  });

  it("returns the explicit mode for dark", () => {
    expect(resolveTheme("dark")).toBe("dark");
  });

  it("returns light when the system reports no dark preference", () => {
    vi.stubGlobal("matchMedia", () => ({ matches: false }) as MediaQueryList);
    expect(resolveTheme("system")).toBe("light");
  });

  it("returns dark when the system reports a dark preference", () => {
    vi.stubGlobal("matchMedia", () => ({ matches: true }) as MediaQueryList);
    expect(resolveTheme("system")).toBe("dark");
  });
});
