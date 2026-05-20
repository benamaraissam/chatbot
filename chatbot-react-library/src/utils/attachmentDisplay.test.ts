import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createBlobUrlFromBase64,
  getImageDisplaySrc,
  registerDisplayUrl,
  revokeAllDisplayUrls,
  revokeDisplayUrl,
  stripClientFieldsFromParts,
  stripClientFieldsFromRequest,
} from "./attachmentDisplay";

const TINY_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9TQ+x9oAAAAASUVORK5CYII=";

describe("attachmentDisplay", () => {
  beforeEach(() => {
    // Reset the module-internal Set by revoking everything between tests.
    revokeAllDisplayUrls();
  });

  afterEach(() => {
    revokeAllDisplayUrls();
    vi.restoreAllMocks();
  });

  describe("registerDisplayUrl / revokeDisplayUrl", () => {
    it("only tracks blob: URLs", () => {
      const spy = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
      registerDisplayUrl("https://example.com/x.png");
      revokeDisplayUrl("https://example.com/x.png");
      // Non-blob URLs are never revoked.
      expect(spy).not.toHaveBeenCalled();
    });

    it("revokes blob: URLs through URL.revokeObjectURL", () => {
      const spy = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
      registerDisplayUrl("blob:fake-1");
      revokeDisplayUrl("blob:fake-1");
      expect(spy).toHaveBeenCalledWith("blob:fake-1");
    });
  });

  describe("createBlobUrlFromBase64", () => {
    it("creates a blob URL for valid base64 payload", () => {
      const url = createBlobUrlFromBase64("image/png", TINY_PNG);
      expect(url).toMatch(/^blob:/);
    });

    it("returns null for empty payload", () => {
      expect(createBlobUrlFromBase64("image/png", "")).toBeNull();
    });

    it("returns null for malformed base64", () => {
      // atob() throws on bad input; the helper must catch and return null.
      expect(createBlobUrlFromBase64("image/png", "!!!not-base64!!!")).toBeNull();
    });
  });

  describe("getImageDisplaySrc", () => {
    it("returns the existing displayUrl when present", () => {
      const src = getImageDisplaySrc({
        type: "image",
        mimeType: "image/png",
        data: TINY_PNG,
        displayUrl: "blob:already-have",
      });
      expect(src).toBe("blob:already-have");
    });

    it("builds a blob URL from base64 when displayUrl is missing", () => {
      const src = getImageDisplaySrc({
        type: "image",
        mimeType: "image/png",
        data: TINY_PNG,
      });
      expect(src).toMatch(/^blob:/);
    });

    it("returns null when no data is available", () => {
      const src = getImageDisplaySrc({
        type: "image",
        mimeType: "image/png",
        data: "",
      });
      expect(src).toBeNull();
    });
  });

  describe("stripClientFieldsFromParts / stripClientFieldsFromRequest", () => {
    it("removes displayUrl from image parts", () => {
      const parts = stripClientFieldsFromParts([
        {
          type: "image",
          mimeType: "image/png",
          data: TINY_PNG,
          displayUrl: "blob:abc",
        },
        { type: "text", text: "hi" },
      ]);
      expect((parts[0] as { displayUrl?: string }).displayUrl).toBeUndefined();
      expect(parts[1]).toEqual({ type: "text", text: "hi" });
    });

    it("preserves non-image parts as-is", () => {
      const file = {
        type: "file" as const,
        name: "a.pdf",
        mimeType: "application/pdf",
        data: "JVBERi0",
      };
      const parts = stripClientFieldsFromParts([file]);
      expect(parts[0]).toEqual(file);
    });

    it("returns a new object from stripClientFieldsFromRequest with cleaned parts", () => {
      const request = {
        conversationId: "c1",
        messages: [
          {
            id: "m_1",
            role: "user" as const,
            parts: [
              {
                type: "image" as const,
                mimeType: "image/png",
                data: TINY_PNG,
                displayUrl: "blob:abc",
              },
            ],
          },
        ],
      };
      const out = stripClientFieldsFromRequest(request);
      expect(out).not.toBe(request);
      expect(
        (out.messages[0].parts[0] as { displayUrl?: string }).displayUrl,
      ).toBeUndefined();
    });
  });
});
