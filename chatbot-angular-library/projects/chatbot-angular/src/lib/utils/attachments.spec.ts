import {
  DEFAULT_ATTACHMENT_ACCEPT,
  attachmentPartsOnly,
  detachPendingAttachments,
  validateAttachmentBatch,
  withImageDefaultText,
} from './attachments';
import type { FilePart, ImagePart, MessagePart, TextPart } from '../types';

function makeFile(name: string, sizeBytes: number, type = ''): File {
  // Build a File of approximately the requested size.
  const blob = new Uint8Array(sizeBytes);
  return new File([blob], name, { type });
}

describe('DEFAULT_ATTACHMENT_ACCEPT', () => {
  it('includes image/* and common text formats', () => {
    expect(DEFAULT_ATTACHMENT_ACCEPT).toContain('image/*');
    expect(DEFAULT_ATTACHMENT_ACCEPT).toContain('.pdf');
    expect(DEFAULT_ATTACHMENT_ACCEPT).toContain('.json');
  });
});

describe('validateAttachmentBatch', () => {
  it('returns null when files are within limits', () => {
    const files = [makeFile('a.png', 100, 'image/png')];
    expect(validateAttachmentBatch(files)).toBeNull();
  });

  it('rejects when count exceeds maxCount', () => {
    const files = [
      makeFile('a.png', 10),
      makeFile('b.png', 10),
      makeFile('c.png', 10),
    ];
    const msg = validateAttachmentBatch(files, { maxCount: 2 });
    expect(msg).toContain('at most 2');
  });

  it('uses singular wording when maxCount is 1', () => {
    const files = [makeFile('a.png', 10), makeFile('b.png', 10)];
    const msg = validateAttachmentBatch(files, { maxCount: 1 });
    expect(msg).toContain('at most 1 file');
    expect(msg).not.toContain('files');
  });

  it('rejects when any file exceeds maxSizeBytes', () => {
    const files = [makeFile('big.png', 2_000_000, 'image/png')];
    const msg = validateAttachmentBatch(files, { maxSizeBytes: 1_000_000 });
    expect(msg).toContain('big.png');
    expect(msg).toContain('size limit');
  });

  it('applies sensible defaults when no options are given', () => {
    // Single tiny file should always pass the defaults.
    const files = [makeFile('x.png', 100, 'image/png')];
    expect(validateAttachmentBatch(files)).toBeNull();
  });
});

describe('attachmentPartsOnly', () => {
  const text: TextPart = { type: 'text', text: 'hi' };
  const image: ImagePart = { type: 'image', mimeType: 'image/png', data: 'AAA' };
  const file: FilePart = { type: 'file', name: 'a.pdf', mimeType: 'application/pdf', data: 'AAA' };

  it('keeps image and file parts; drops text', () => {
    const out = attachmentPartsOnly([text, image, file]);
    expect(out).toEqual([image, file]);
  });

  it('returns an empty array when no attachments are present', () => {
    expect(attachmentPartsOnly([text])).toEqual([]);
  });
});

describe('detachPendingAttachments', () => {
  it('returns only the text parts', () => {
    const text: TextPart = { type: 'text', text: 'hi' };
    const image: ImagePart = { type: 'image', mimeType: 'image/png', data: 'AAA' };
    expect(detachPendingAttachments([text, image])).toEqual([text]);
  });
});

describe('withImageDefaultText', () => {
  const image: ImagePart = { type: 'image', mimeType: 'image/png', data: 'AAA' };

  it('prepends the user text when present', () => {
    const parts = withImageDefaultText('describe this', [image]);
    expect(parts[0]).toEqual({ type: 'text', text: 'describe this' });
    expect(parts[1]).toBe(image);
  });

  it('does not add a text part when the user text is empty', () => {
    const parts = withImageDefaultText('', [image]);
    expect(parts).toEqual([image]);
  });
});
