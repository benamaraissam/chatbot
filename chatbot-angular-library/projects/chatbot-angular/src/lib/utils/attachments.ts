import type { FilePart, ImagePart, MessagePart, TextPart } from '../types';

export const DEFAULT_ATTACHMENT_ACCEPT =
  'image/*,.pdf,.txt,.csv,.md,.json,.xml,.docx,.xlsx,.pptx';

export interface PendingAttachment {
  id: string;
  file: File;
  previewUrl?: string;
  status: 'pending' | 'uploading' | 'ready' | 'error';
  error?: string;
}

/** Convert File objects into base64-encoded MessagePart arrays. */
export async function filesToAttachmentParts(files: File[]): Promise<MessagePart[]> {
  const parts: MessagePart[] = [];
  for (const file of files) {
    const data = await fileToBase64(file);
    if (file.type.startsWith('image/')) {
      const part: ImagePart = {
        type: 'image',
        mimeType: file.type,
        data,
        name: file.name,
        displayUrl: URL.createObjectURL(file),
      };
      parts.push(part);
    } else {
      const part: FilePart = {
        type: 'file',
        name: file.name,
        mimeType: file.type,
        data,
      };
      parts.push(part);
    }
  }
  return parts;
}

/** Extract only image/file parts from a PendingAttachment array. */
export function pendingAttachmentsToParts(attachments: PendingAttachment[]): MessagePart[] {
  // This is meant to be called after filesToAttachmentParts; returns empty until resolved
  return [];
}

/** Return only image/file parts from a MessagePart array. */
export function attachmentPartsOnly(parts: MessagePart[]): Array<ImagePart | FilePart> {
  return parts.filter((p): p is ImagePart | FilePart => p.type === 'image' || p.type === 'file');
}

/** Remove attachment parts from a MessagePart array, returning only text parts. */
export function detachPendingAttachments(parts: MessagePart[]): TextPart[] {
  return parts.filter((p): p is TextPart => p.type === 'text');
}

export interface ValidateAttachmentOptions {
  maxCount?: number;
  maxSizeBytes?: number;
}

/**
 * Validate a batch of files against count and size limits.
 * Returns an error string if invalid, or null if valid.
 */
export function validateAttachmentBatch(
  files: File[],
  options: ValidateAttachmentOptions = {},
): string | null {
  const { maxCount = 5, maxSizeBytes = 10 * 1024 * 1024 } = options;
  if (files.length > maxCount) {
    return `You can attach at most ${maxCount} file${maxCount === 1 ? '' : 's'} at a time.`;
  }
  for (const file of files) {
    if (file.size > maxSizeBytes) {
      const mb = (maxSizeBytes / (1024 * 1024)).toFixed(0);
      return `"${file.name}" exceeds the ${mb} MB size limit.`;
    }
  }
  return null;
}

/** Revoke blob URLs for all pending attachments. */
export function revokeAttachmentPreviews(attachments: PendingAttachment[]): void {
  for (const a of attachments) {
    if (a.previewUrl) {
      try { URL.revokeObjectURL(a.previewUrl); } catch { /* ignore */ }
    }
  }
}

/**
 * If text is empty and there are image parts, add a default text part.
 * Returns a combined MessagePart array suitable for a user message.
 */
export function withImageDefaultText(text: string, attachmentParts: MessagePart[]): MessagePart[] {
  const parts: MessagePart[] = [];
  if (text) {
    parts.push({ type: 'text', text });
  }
  parts.push(...attachmentParts);
  return parts;
}

// ── internal helper ───────────────────────────────────────────────────────────

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Strip the data URL prefix (e.g. "data:image/png;base64,")
      const base64 = result.split(',')[1] ?? result;
      resolve(base64);
    };
    reader.onerror = () => reject(new Error(`Failed to read file: ${file.name}`));
    reader.readAsDataURL(file);
  });
}
