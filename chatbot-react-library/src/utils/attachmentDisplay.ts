import type { ImagePart, Message, MessagePart } from "../types";
import { partBase64Payload } from "./messageParts";

const ownedBlobUrls = new Set<string>();

export function registerDisplayUrl(url: string): void {
  if (url.startsWith("blob:")) ownedBlobUrls.add(url);
}

export function revokeDisplayUrl(url: string | undefined): void {
  if (!url || !ownedBlobUrls.has(url)) return;
  URL.revokeObjectURL(url);
  ownedBlobUrls.delete(url);
}

export function revokeAllDisplayUrls(): void {
  for (const url of ownedBlobUrls) URL.revokeObjectURL(url);
  ownedBlobUrls.clear();
}

export function revokeMessageDisplayUrls(message: Message): void {
  for (const part of message.parts) {
    if (part.type === "image") revokeDisplayUrl(part.displayUrl);
  }
}

export function createBlobUrlFromBase64(mimeType: string, data: string): string | null {
  const payload = partBase64Payload(data);
  if (!payload) return null;
  try {
    const binary = atob(payload);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const url = URL.createObjectURL(new Blob([bytes], { type: mimeType || "image/jpeg" }));
    registerDisplayUrl(url);
    return url;
  } catch {
    return null;
  }
}

export function getImageDisplaySrc(part: ImagePart): string | null {
  if (part.displayUrl) return part.displayUrl;
  if (part.data?.trim()) return createBlobUrlFromBase64(part.mimeType, part.data);
  return null;
}

export function stripClientFieldsFromParts(parts: MessagePart[]): MessagePart[] {
  return parts.map((part) => {
    if (part.type !== "image" || !part.displayUrl) return part;
    const { displayUrl: _removed, ...rest } = part;
    return rest;
  });
}

export function stripClientFieldsFromRequest<T extends { messages: Message[] }>(
  body: T,
): T {
  return {
    ...body,
    messages: body.messages.map((message) => ({
      ...message,
      parts: stripClientFieldsFromParts(message.parts),
    })),
  };
}
