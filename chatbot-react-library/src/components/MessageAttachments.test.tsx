import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageAttachments } from "./MessageAttachments";
import type { FilePart, ImagePart, TextPart } from "../types";

const text: TextPart = { type: "text", text: "ignored" };
const image: ImagePart = {
  type: "image",
  mimeType: "image/png",
  data: "AAA",
  name: "logo.png",
};
const imageFile: FilePart = {
  type: "file",
  name: "selfie.jpg",
  mimeType: "image/jpeg",
  data: "AAA",
};
const pdfFile: FilePart = {
  type: "file",
  name: "doc.pdf",
  mimeType: "application/pdf",
  data: "JVBERi0",
};
const emptyFile: FilePart = {
  type: "file",
  name: "missing.txt",
  mimeType: "text/plain",
  data: "",
};

describe("<MessageAttachments />", () => {
  it("renders nothing when no attachment parts are provided", () => {
    const { container } = render(<MessageAttachments parts={[text]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders an image figure with caption from name", () => {
    render(<MessageAttachments parts={[image]} />);
    // The caption shows the file name.
    expect(screen.getByText("logo.png")).toBeInTheDocument();
  });

  it("treats an image-MIME FilePart as an image figure", () => {
    const { container } = render(<MessageAttachments parts={[imageFile]} />);
    expect(container.querySelector(".cb-attachment--image")).not.toBeNull();
  });

  it("renders a downloadable anchor for non-image files with data", () => {
    render(<MessageAttachments parts={[pdfFile]} />);
    const link = screen.getByTitle(/Download doc\.pdf/i) as HTMLAnchorElement;
    expect(link.href).toContain("application/pdf");
    expect(link.getAttribute("download")).toBe("doc.pdf");
  });

  it("renders a non-clickable tile for non-image files without data", () => {
    const { container } = render(<MessageAttachments parts={[emptyFile]} />);
    expect(container.querySelector("a.cb-attachment")).toBeNull();
    expect(container.querySelector("div.cb-attachment--file")).not.toBeNull();
  });

  it("applies the user variant root class by default", () => {
    const { container } = render(<MessageAttachments parts={[image]} />);
    expect(container.querySelector(".cb-user-attachments")).not.toBeNull();
  });

  it("applies the assistant variant root class when requested", () => {
    const { container } = render(
      <MessageAttachments parts={[image]} variant="assistant" />,
    );
    expect(
      container.querySelector(".cb-message-attachments--assistant"),
    ).not.toBeNull();
  });
});
