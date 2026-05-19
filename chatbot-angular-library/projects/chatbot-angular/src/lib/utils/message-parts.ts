import type { FilePart, ImagePart, Message, MessagePart, TextPart } from '../types';

export function isTextPart(part: MessagePart): part is TextPart { return part.type === 'text'; }
export function isImagePart(part: MessagePart): part is ImagePart { return part.type === 'image'; }
export function isFilePart(part: MessagePart): part is FilePart { return part.type === 'file'; }
export function isImageLikePart(part: MessagePart): part is ImagePart | FilePart {
  if (part.type === 'image') return true;
  if (part.type === 'file') return part.mimeType.startsWith('image/');
  return false;
}
export function getMessageText(message: Message): string {
  return message.parts.filter(isTextPart).map((p) => p.text).join('\n').trim();
}
export function partBase64Payload(data: string): string {
  return data.includes(',') ? data.split(',', 2)[1]! : data;
}
export function imagePartDataUrl(part: ImagePart | FilePart): string {
  const mime = part.type === 'image' ? part.mimeType : part.mimeType || 'image/jpeg';
  return `data:${mime};base64,${partBase64Payload(part.data)}`;
}
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
