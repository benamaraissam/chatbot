import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AttachmentImage } from "./AttachmentImage";

const TINY_PNG =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9TQ+x9oAAAAASUVORK5CYII=";

describe("<AttachmentImage />", () => {
  it("renders an <img> when a displayUrl is already present", () => {
    render(
      <AttachmentImage
        part={{
          type: "image",
          mimeType: "image/png",
          data: TINY_PNG,
          displayUrl: "blob:already-set",
          name: "logo.png",
        }}
      />,
    );
    const img = screen.getByAltText("logo.png") as HTMLImageElement;
    expect(img.src).toBe("blob:already-set");
  });

  it("renders an <img> built from base64 when only data is available", () => {
    render(
      <AttachmentImage
        part={{
          type: "image",
          mimeType: "image/png",
          data: TINY_PNG,
        }}
      />,
    );
    const img = screen.getByAltText("Image") as HTMLImageElement;
    expect(img.src).toMatch(/^blob:/);
  });

  it("renders an unavailable status when there is no data and no displayUrl", () => {
    render(
      <AttachmentImage
        part={{
          type: "image",
          mimeType: "image/png",
          data: "",
        }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/unavailable/i);
  });
});
