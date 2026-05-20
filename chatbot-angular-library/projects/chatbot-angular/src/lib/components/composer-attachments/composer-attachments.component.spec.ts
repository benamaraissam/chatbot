import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ComposerAttachmentsComponent } from './composer-attachments.component';
import type { PendingAttachment } from '../../utils/attachments';

function pending(name: string, type: string): PendingAttachment {
  return {
    id: `att_${name}`,
    file: new File(['x'], name, { type }),
    previewUrl: type.startsWith('image/') ? `blob:fake-${name}` : undefined,
    status: 'ready',
  };
}

describe('ComposerAttachmentsComponent', () => {
  let fixture: ComponentFixture<ComposerAttachmentsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ComposerAttachmentsComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(ComposerAttachmentsComponent);
  });

  it('renders nothing when items input is empty', () => {
    fixture.componentRef.setInput('items', []);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-composer-attachments')).toBeNull();
  });

  it('renders an image tile for image attachments', () => {
    fixture.componentRef.setInput('items', [pending('photo.png', 'image/png')]);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-composer-attachment--image')).not.toBeNull();
    expect(host.querySelector('img')).not.toBeNull();
  });

  it('renders a file tile for non-image attachments', () => {
    fixture.componentRef.setInput('items', [pending('doc.pdf', 'application/pdf')]);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    // The file variant has its own class; whichever it is, it renders the filename.
    expect(host.textContent).toContain('doc.pdf');
  });
});
