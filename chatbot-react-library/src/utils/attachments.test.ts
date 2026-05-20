import { describe, expect, it } from "vitest";
import {
  DEFAULT_ATTACHMENT_ACCEPT,
  fileExtension,
  inferImageMimeType,
  isImageFile,
  normalizeMimeType,
} from "./attachments";

describe("fileExtension", () => {
  it("returns the lowercase extension including the dot", () => {
    expect(fileExtension("photo.PNG")).toBe(".png");
    expect(fileExtension("DOC.pdf")).toBe(".pdf");
  });

  it("returns empty string when no extension is present", () => {
    expect(fileExtension("noext")).toBe("");
  });
});

describe("normalizeMimeType", () => {
  it("strips parameters and lowercases", () => {
    expect(normalizeMimeType("Text/HTML; charset=utf-8")).toBe("text/html");
  });

  it("returns empty string for blank input", () => {
    expect(normalizeMimeType("")).toBe("");
  });
});

describe("inferImageMimeType", () => {
  function fakeFile(name: string, type = ""): File {
    return new File(["x"], name, { type });
  }

  it("uses the file MIME when already image/*", () => {
    expect(inferImageMimeType(fakeFile("p.png", "image/png"))).toBe("image/png");
  });

  it("falls back to the extension mapping when MIME is missing", () => {
    expect(inferImageMimeType(fakeFile("p.heic"))).toBe("image/heic");
    expect(inferImageMimeType(fakeFile("p.jpg"))).toBe("image/jpeg");
  });

  it("defaults to image/jpeg for unknown extensions", () => {
    expect(inferImageMimeType(fakeFile("mystery"))).toBe("image/jpeg");
  });
});

describe("isImageFile", () => {
  function fakeFile(name: string, type = ""): File {
    return new File(["x"], name, { type });
  }

  it("returns true for image/* MIME", () => {
    expect(isImageFile(fakeFile("p.png", "image/png"))).toBe(true);
  });

  it("returns false for text/* MIME even with image extension", () => {
    expect(isImageFile(fakeFile("p.svg", "text/plain"))).toBe(false);
  });

  it("returns true for image extension with empty/octet-stream MIME", () => {
    expect(isImageFile(fakeFile("p.png", ""))).toBe(true);
    expect(isImageFile(fakeFile("p.png", "application/octet-stream"))).toBe(true);
  });

  it("returns false for non-image extensions", () => {
    expect(isImageFile(fakeFile("doc.pdf", ""))).toBe(false);
  });
});

describe("DEFAULT_ATTACHMENT_ACCEPT", () => {
  it("includes both image/* and common text formats", () => {
    expect(DEFAULT_ATTACHMENT_ACCEPT).toContain("image/*");
    expect(DEFAULT_ATTACHMENT_ACCEPT).toContain(".pdf");
    expect(DEFAULT_ATTACHMENT_ACCEPT).toContain(".json");
  });
});
