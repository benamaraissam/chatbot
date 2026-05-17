import type { FilePart, ImagePart, MessagePart } from "../types";
import { formatFileSize } from "./messageParts";

export interface AttachmentLimits {
  maxCount?: number;
  maxSizeBytes?: number;
}

export interface PendingAttachment {
  id: string;
  file: File;
  previewUrl: string | null;
  part: ImagePart | FilePart;
}

const DEFAULT_MAX_COUNT = 5;
const DEFAULT_MAX_SIZE = 5 * 1024 * 1024;

const DEFAULT_ACCEPT =
  "image/*,.pdf,.txt,.md,.json,.csv,.html,.css,.js,.ts,.tsx,.py,.xml,.yaml,.yml";

export const DEFAULT_ATTACHMENT_ACCEPT = DEFAULT_ACCEPT;

const IMAGE_EXTENSIONS = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".webp",
  ".bmp",
  ".svg",
  ".heic",
  ".heif",
  ".avif",
]);

const EXT_TO_MIME: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".bmp": "image/bmp",
  ".svg": "image/svg+xml",
  ".heic": "image/heic",
  ".heif": "image/heif",
  ".avif": "image/avif",
};

export function fileExtension(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

export function normalizeMimeType(mime: string): string {
  return mime.split(";")[0]?.trim().toLowerCase() || "";
}

export function inferImageMimeType(file: File): string {
  const base = normalizeMimeType(file.type);
  if (base.startsWith("image/")) return base;
  const ext = fileExtension(file.name);
  return EXT_TO_MIME[ext] ?? "image/jpeg";
}

export function isImageFile(file: File): boolean {
  const base = normalizeMimeType(file.type);
  if (base.startsWith("text/")) return false;
  if (base.startsWith("image/")) return true;
  const ext = fileExtension(file.name);
  if (!IMAGE_EXTENSIONS.has(ext)) return false;
  // Trust extension only when the browser did not label the file as plain text.
  return !base || base === "application/octet-stream";
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== "string") {
        reject(new Error("Failed to read file"));
        return;
      }
      const base64 = result.includes(",") ? result.split(",", 2)[1]! : result;
      resolve(base64);
    };
    reader.onerror = () => reject(reader.error ?? new Error("Failed to read file"));
    reader.readAsDataURL(file);
  });
}

export function validateAttachmentBatch(
  files: File[],
  currentCount: number,
  limits?: AttachmentLimits,
): string | null {
  const maxCount = limits?.maxCount ?? DEFAULT_MAX_COUNT;
  const maxSize = limits?.maxSizeBytes ?? DEFAULT_MAX_SIZE;

  if (currentCount + files.length > maxCount) {
    return `You can attach up to ${maxCount} files.`;
  }
  for (const file of files) {
    if (file.size > maxSize) {
      return `"${file.name}" is too large (max ${formatFileSize(maxSize)}).`;
    }
  }
  return null;
}

export async function filesToAttachmentParts(
  files: File[],
  createId: () => string,
): Promise<PendingAttachment[]> {
  const items: PendingAttachment[] = [];
  for (const file of files) {
    const data = await readFileAsBase64(file);
    const id = createId();
    if (isImageFile(file)) {
      const part: ImagePart = {
        type: "image",
        mimeType: inferImageMimeType(file),
        data,
        name: file.name,
      };
      items.push({
        id,
        file,
        previewUrl: URL.createObjectURL(file),
        part,
      });
    } else {
      const part: FilePart = {
        type: "file",
        name: file.name,
        mimeType: file.type || "application/octet-stream",
        data,
      };
      items.push({
        id,
        file,
        previewUrl: null,
        part,
      });
    }
  }
  return items;
}

export function revokeAttachmentPreviews(items: PendingAttachment[]): void {
  for (const item of items) {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
  }
}

export function attachmentPartsOnly(items: PendingAttachment[]): MessagePart[] {
  return items.map((a) => a.part);
}

/** Build message parts from pending items; transfers blob preview URLs to `displayUrl`. */
export function pendingAttachmentsToParts(
  items: PendingAttachment[],
): MessagePart[] {
  return items.map((item) => {
    if (item.part.type === "image" && item.previewUrl) {
      return { ...item.part, displayUrl: item.previewUrl };
    }
    return item.part;
  });
}

/** Clear pending list without revoking blob URLs (ownership moved to a message). */
export function detachPendingAttachments(items: PendingAttachment[]): void {
  for (const item of items) {
    item.previewUrl = null;
  }
}

/** Default user text when sending image-only (required by many vision APIs). */
export const IMAGE_ONLY_DEFAULT_PROMPT = "What is in this image?";

export function withImageDefaultText(
  text: string,
  parts: MessagePart[],
): MessagePart[] {
  const hasImage = parts.some(
    (p) =>
      p.type === "image" ||
      (p.type === "file" && p.mimeType.startsWith("image/")),
  );
  const hasText = Boolean(text.trim()) || parts.some((p) => p.type === "text");
  if (!hasImage || hasText) {
    return [
      ...(text.trim() ? [{ type: "text" as const, text: text.trim() }] : []),
      ...parts,
    ];
  }
  return [
    { type: "text", text: IMAGE_ONLY_DEFAULT_PROMPT },
    ...parts,
  ];
}
