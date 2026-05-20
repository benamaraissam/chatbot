import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MessageAttachmentsComponent } from './message-attachments.component';
import type { FilePart, ImagePart, MessagePart, TextPart } from '../../types';

const text: TextPart = { type: 'text', text: 'ignored' };
const image: ImagePart = {
  type: 'image',
  mimeType: 'image/png',
  data: 'AAA',
  name: 'logo.png',
  displayUrl: 'blob:abc',
};
const imageFile: FilePart = {
  type: 'file',
  name: 'selfie.jpg',
  mimeType: 'image/jpeg',
  data: 'AAA',
};
const pdfFile: FilePart = {
  type: 'file',
  name: 'doc.pdf',
  mimeType: 'application/pdf',
  data: 'JVBERi0',
};
const emptyFile: FilePart = {
  type: 'file',
  name: 'missing.txt',
  mimeType: 'text/plain',
  data: '',
};

describe('MessageAttachmentsComponent', () => {
  let fixture: ComponentFixture<MessageAttachmentsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MessageAttachmentsComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(MessageAttachmentsComponent);
  });

  function setParts(parts: MessagePart[]): void {
    fixture.componentRef.setInput('parts', parts);
    fixture.detectChanges();
  }

  it('renders nothing when there are no attachment parts', () => {
    setParts([text]);
    const host: HTMLElement = fixture.nativeElement;
    expect(host.firstElementChild).toBeNull();
  });

  it('renders an image figure with a caption', () => {
    setParts([image]);
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-attachment--image')).not.toBeNull();
    expect(host.textContent).toContain('logo.png');
    expect(host.querySelector('img')).not.toBeNull();
  });

  it('renders an image-MIME FilePart as an image figure', () => {
    setParts([imageFile]);
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-attachment--image')).not.toBeNull();
  });

  it('renders a downloadable anchor for non-image files with data', () => {
    setParts([pdfFile]);
    const host: HTMLElement = fixture.nativeElement;
    const anchor = host.querySelector(
      'a.cb-attachment--downloadable',
    ) as HTMLAnchorElement | null;
    expect(anchor).not.toBeNull();
    expect(anchor!.getAttribute('download')).toBe('doc.pdf');
    expect(anchor!.href).toContain('application/pdf');
  });

  it('renders a non-clickable file tile for empty-data files', () => {
    setParts([emptyFile]);
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('a.cb-attachment--downloadable')).toBeNull();
    expect(host.querySelector('div.cb-attachment--file')).not.toBeNull();
  });

  it('uses the user variant root class by default', () => {
    setParts([image]);
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-user-attachments')).not.toBeNull();
  });

  it('uses the assistant variant root class when requested', () => {
    fixture.componentRef.setInput('parts', [image]);
    fixture.componentRef.setInput('variant', 'assistant');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(
      host.querySelector('.cb-message-attachments--assistant'),
    ).not.toBeNull();
  });

  it('uses the inline variant root class when requested', () => {
    fixture.componentRef.setInput('parts', [image]);
    fixture.componentRef.setInput('variant', 'inline');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(
      host.querySelector('.cb-message-attachments--inline'),
    ).not.toBeNull();
  });
});
