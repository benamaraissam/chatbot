import {
  getImageDisplaySrc,
  registerDisplayUrl,
  revokeAllDisplayUrls,
  stripClientFieldsFromRequest,
} from './attachment-display';
import type { ImagePart, Message } from '../types';

describe('getImageDisplaySrc', () => {
  it('returns the displayUrl when present', () => {
    const src = getImageDisplaySrc({
      type: 'image',
      mimeType: 'image/png',
      data: 'AAA',
      displayUrl: 'blob:already',
    });
    expect(src).toBe('blob:already');
  });

  it('falls back to a data URL when displayUrl is missing', () => {
    const src = getImageDisplaySrc({
      type: 'image',
      mimeType: 'image/png',
      data: 'AAA',
    });
    expect(src).toBe('data:image/png;base64,AAA');
  });
});

describe('registerDisplayUrl / revokeAllDisplayUrls', () => {
  it('revokeAllDisplayUrls drains the registry without throwing', () => {
    registerDisplayUrl('blob:fake-1');
    registerDisplayUrl('blob:fake-2');
    // No assertion on URL.revokeObjectURL — jsdom may throw, but the
    // helper catches and continues. We assert it completes.
    expect(() => revokeAllDisplayUrls()).not.toThrow();
  });
});

describe('stripClientFieldsFromRequest', () => {
  it('removes displayUrl from image parts in the messages', () => {
    const request = {
      conversationId: 'c1',
      messages: [
        {
          id: 'm_1',
          role: 'user' as const,
          parts: [
            {
              type: 'image' as const,
              mimeType: 'image/png',
              data: 'AAA',
              displayUrl: 'blob:abc',
            } as ImagePart,
            { type: 'text' as const, text: 'hi' },
          ],
        },
      ],
    };
    const out = stripClientFieldsFromRequest(request);
    const cleaned = out.messages[0].parts[0] as ImagePart;
    expect(cleaned.displayUrl).toBeUndefined();
    expect(out.messages[0].parts[1]).toEqual({ type: 'text', text: 'hi' });
  });

  it('returns a different object (does not mutate input)', () => {
    const original: { messages: Message[] } = { messages: [] };
    const out = stripClientFieldsFromRequest(original);
    expect(out).not.toBe(original);
  });
});
