import type { FilePart, ImagePart, Message, TextPart } from '../types';
import {
  formatFileSize,
  getMessageText,
  imagePartDataUrl,
  isFilePart,
  isImageLikePart,
  isImagePart,
  isTextPart,
  partBase64Payload,
} from './message-parts';

const textPart: TextPart = { type: 'text', text: 'hello' };
const imagePart: ImagePart = {
  type: 'image',
  mimeType: 'image/png',
  data: 'iVBORw0KGgoAAAANSUhEUgAAA',
};
const filePart: FilePart = {
  type: 'file',
  name: 'doc.pdf',
  mimeType: 'application/pdf',
  data: 'JVBERi0',
};
const imageFilePart: FilePart = {
  type: 'file',
  name: 'selfie.jpg',
  mimeType: 'image/jpeg',
  data: '/9j/4AAQ',
};

describe('message-parts type guards', () => {
  it('isTextPart only matches text parts', () => {
    expect(isTextPart(textPart)).toBeTrue();
    expect(isTextPart(imagePart)).toBeFalse();
    expect(isTextPart(filePart)).toBeFalse();
  });

  it('isImagePart only matches image parts', () => {
    expect(isImagePart(imagePart)).toBeTrue();
    expect(isImagePart(filePart)).toBeFalse();
  });

  it('isFilePart only matches file parts', () => {
    expect(isFilePart(filePart)).toBeTrue();
    expect(isFilePart(imagePart)).toBeFalse();
  });

  it('isImageLikePart accepts image parts and file parts with image MIME', () => {
    expect(isImageLikePart(imagePart)).toBeTrue();
    expect(isImageLikePart(imageFilePart)).toBeTrue();
    expect(isImageLikePart(filePart)).toBeFalse();
    expect(isImageLikePart(textPart)).toBeFalse();
  });
});

describe('getMessageText', () => {
  it('joins text parts with newlines and trims whitespace', () => {
    const msg: Message = {
      id: 'm_1',
      role: 'user',
      parts: [
        { type: 'text', text: '  hello' },
        { type: 'image', mimeType: 'image/png', data: 'x' },
        { type: 'text', text: 'world  ' },
      ],
    };
    expect(getMessageText(msg)).toBe('hello\nworld');
  });

  it('returns empty string when no text parts exist', () => {
    const msg: Message = { id: 'm_1', role: 'user', parts: [imagePart] };
    expect(getMessageText(msg)).toBe('');
  });
});

describe('partBase64Payload', () => {
  it('returns the raw payload when no data: prefix is present', () => {
    expect(partBase64Payload('iVBORw0KGgo')).toBe('iVBORw0KGgo');
  });

  it('strips a data URL prefix and returns just the payload', () => {
    expect(partBase64Payload('data:image/png;base64,iVBORw0KGgo')).toBe(
      'iVBORw0KGgo',
    );
  });
});

describe('imagePartDataUrl', () => {
  it('builds a data URL from an ImagePart', () => {
    expect(imagePartDataUrl(imagePart)).toBe(
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA',
    );
  });

  it('falls back to image/jpeg for a FilePart without a MIME type', () => {
    const bare: FilePart = { type: 'file', name: 'x', mimeType: '', data: 'abc' };
    expect(imagePartDataUrl(bare)).toBe('data:image/jpeg;base64,abc');
  });
});

describe('formatFileSize', () => {
  it('formats bytes', () => {
    expect(formatFileSize(0)).toBe('0 B');
    expect(formatFileSize(1023)).toBe('1023 B');
  });

  it('formats kilobytes with one decimal', () => {
    expect(formatFileSize(2048)).toBe('2.0 KB');
  });

  it('formats megabytes with one decimal', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1.0 MB');
    expect(formatFileSize(2.5 * 1024 * 1024)).toBe('2.5 MB');
  });
});
