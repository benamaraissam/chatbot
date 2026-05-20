import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  clearConversation,
  loadConversation,
  saveConversation,
} from "./storage";

const KEY = "chatbot-react-test:conv";

describe("conversation storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    localStorage.clear();
  });

  it("returns null when nothing is stored", () => {
    expect(loadConversation(KEY)).toBeNull();
  });

  it("round-trips a simple conversation", () => {
    saveConversation(KEY, {
      conversationId: "c1",
      messages: [
        { id: "m_1", role: "user", parts: [{ type: "text", text: "hi" }] },
      ],
    });
    const loaded = loadConversation(KEY);
    expect(loaded).not.toBeNull();
    expect(loaded?.conversationId).toBe("c1");
    expect(loaded?.messages).toHaveLength(1);
  });

  it("clearConversation removes the stored data", () => {
    saveConversation(KEY, { conversationId: "c2", messages: [] });
    expect(loadConversation(KEY)).not.toBeNull();
    clearConversation(KEY);
    expect(loadConversation(KEY)).toBeNull();
  });

  it("strips oversized image payloads before persisting", () => {
    const big = "x".repeat(200_000);
    saveConversation(KEY, {
      conversationId: "c3",
      messages: [
        {
          id: "m_1",
          role: "user",
          parts: [
            { type: "image", mimeType: "image/png", data: big },
            { type: "text", text: "look" },
          ],
        },
      ],
    });
    const loaded = loadConversation(KEY);
    // Image data is replaced with an empty string so the entry survives
    // localStorage quota limits — the in-memory copy still has it.
    const imagePart = loaded?.messages[0].parts.find((p) => p.type === "image");
    expect(imagePart).toBeDefined();
    expect((imagePart as { data: string }).data).toBe("");
  });

  it("returns null on malformed stored JSON instead of throwing", () => {
    localStorage.setItem(KEY, "not-json{");
    expect(loadConversation(KEY)).toBeNull();
  });
});
