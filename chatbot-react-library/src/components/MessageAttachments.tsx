import { FileText } from "lucide-react";
import type { FilePart, ImagePart, MessagePart } from "../types";
import { isFilePart, isImagePart } from "../utils/messageParts";
import { AttachmentImage } from "./AttachmentImage";

interface MessageAttachmentsProps {
  parts: MessagePart[];
  variant?: "user" | "inline";
}

function isNonImageFile(part: MessagePart): part is FilePart {
  return isFilePart(part) && !part.mimeType.startsWith("image/");
}

export function MessageAttachments({
  parts,
  variant = "user",
}: MessageAttachmentsProps) {
  const images = parts.filter(isImagePart);
  const imageFiles = parts.filter(
    (p) => isFilePart(p) && p.mimeType.startsWith("image/"),
  ) as FilePart[];
  const files = parts.filter(isNonImageFile);

  if (images.length === 0 && imageFiles.length === 0 && files.length === 0) {
    return null;
  }

  const rootClass =
    variant === "user"
      ? "cb-user-attachments"
      : "cb-message-attachments cb-message-attachments--inline";

  const renderImageFigure = (part: ImagePart, key: string) => (
    <figure key={key} className="cb-attachment cb-attachment--image">
      <AttachmentImage part={part} className="cb-attachment-image" />
      {part.name ? (
        <figcaption className="cb-attachment-caption">{part.name}</figcaption>
      ) : null}
    </figure>
  );

  return (
    <div className={rootClass}>
      {images.map((part, i) => renderImageFigure(part, `img-${i}`))}
      {imageFiles.map((part, i) =>
        renderImageFigure(
          {
            type: "image",
            mimeType: part.mimeType,
            data: part.data,
            name: part.name,
          },
          `imgf-${i}`,
        ),
      )}
      {files.map((part, i) => (
        <div
          key={`file-${i}`}
          className="cb-attachment cb-attachment--file"
          title={part.name}
        >
          <FileText size={18} className="cb-attachment-file-icon" aria-hidden />
          <span className="cb-attachment-file-name">{part.name}</span>
          <span className="cb-attachment-file-type">{part.mimeType}</span>
        </div>
      ))}
    </div>
  );
}
