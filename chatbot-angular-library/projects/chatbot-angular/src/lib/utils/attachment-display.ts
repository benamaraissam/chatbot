import type { ImagePart, Message, MessagePart } from '../types';

/** Map of displayUrl -> blobUrl for cleanup. */
const displayUrlRegistry = new Set<string>();

/** Register a display URL for later cleanup. */
export function registerDisplayUrl(url: string): void {
  displayUrlRegistry.add(url);
}

/** Get the display URL for an image part (falls back to data URL). */
export function getImageDisplaySrc(part: ImagePart): string {
  if (part.displayUrl) return part.displayUrl;
  return `data:${part.mimeType};base64,${part.data}`;
}

/** Revoke all tracked display URLs. */
export function revokeAllDisplayUrls(): void {
  for (const url of displayUrlRegistry) {
    try { URL.revokeObjectURL(url); } catch { /* ignore */ }
  }
  displayUrlRegistry.clear();
}

/** Revoke display URLs belonging to a single message. */
export function revokeMessageDisplayUrls(message: Message): void {
  for (const part of message.parts) {
    if (part.type === 'image' && part.displayUrl) {
      try { URL.revokeObjectURL(part.displayUrl); } catch { /* ignore */ }
      displayUrlRegistry.delete(part.displayUrl);
    }
  }
}

/**
 * Strip client-only fields (displayUrl) from a message's parts before
 * sending to the server.
 */
export function stripClientFieldsFromRequest<T extends { messages: Message[] }>(body: T): T {
  return {
    ...body,
    messages: body.messages.map((message) => ({
      ...message,
      parts: message.parts.map((part): MessagePart => {
        if (part.type !== 'image' || !('displayUrl' in part)) return part;
        const { displayUrl: _removed, ...rest } = part as ImagePart;
        return rest as ImagePart;
      }),
    })),
  };
}
