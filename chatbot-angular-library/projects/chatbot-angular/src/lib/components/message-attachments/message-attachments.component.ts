import { Component, ChangeDetectionStrategy, input, computed } from '@angular/core';
import { FilePart, ImagePart, MessagePart } from '../../types';
import { isFilePart, isImagePart } from '../../utils/message-parts';
import { getImageDisplaySrc } from '../../utils/attachment-display';

@Component({
  selector: 'cb-message-attachments',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (images().length > 0 || imageFiles().length > 0 || files().length > 0) {
      <div [class]="rootClass()">
        @for (part of images(); track $index) {
          <figure class="cb-attachment cb-attachment--image">
            @if (imgSrc(part); as src) {
              <img [src]="src" [alt]="part.name || 'Image'" class="cb-attachment-image" />
            } @else {
              <div class="cb-attachment-image-missing">Image unavailable</div>
            }
            @if (part.name) {
              <figcaption class="cb-attachment-caption">{{ part.name }}</figcaption>
            }
          </figure>
        }
        @for (part of imageFiles(); track $index) {
          <figure class="cb-attachment cb-attachment--image">
            <img [src]="fileImgSrc(part)" [alt]="part.name || 'Image'" class="cb-attachment-image" />
            @if (part.name) {
              <figcaption class="cb-attachment-caption">{{ part.name }}</figcaption>
            }
          </figure>
        }
        @for (part of files(); track $index) {
          @if (part.data) {
            <a
              class="cb-attachment cb-attachment--file cb-attachment--downloadable"
              [href]="'data:' + part.mimeType + ';base64,' + part.data"
              [download]="part.name"
              [title]="'Download ' + part.name"
            >
              <!-- FileText icon -->
              <svg class="cb-attachment-file-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              <span class="cb-attachment-file-name">{{ part.name }}</span>
              <span class="cb-attachment-file-type">{{ part.mimeType }}</span>
              <!-- Download icon -->
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </a>
          } @else {
            <div class="cb-attachment cb-attachment--file" [title]="part.name">
              <svg class="cb-attachment-file-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span class="cb-attachment-file-name">{{ part.name }}</span>
              <span class="cb-attachment-file-type">{{ part.mimeType }}</span>
            </div>
          }
        }
      </div>
    }
  `,
  styles: [`
    .cb-attachment--downloadable {
      text-decoration: none;
      cursor: pointer;
      transition: border-color 0.15s ease, background 0.15s ease;
    }
    .cb-attachment--downloadable:hover {
      border-color: var(--cb-primary);
      background: var(--cb-primary-muted);
    }
  `],
})
export class MessageAttachmentsComponent {
  readonly parts = input<MessagePart[]>([]);
  readonly variant = input<'user' | 'inline' | 'assistant'>('user');

  readonly images = computed(() => this.parts().filter(isImagePart) as ImagePart[]);
  readonly imageFiles = computed(() => this.parts().filter(p => isFilePart(p) && p.mimeType.startsWith('image/')) as FilePart[]);
  readonly files = computed(() => this.parts().filter(p => isFilePart(p) && !p.mimeType.startsWith('image/')) as FilePart[]);

  readonly rootClass = computed(() =>
    this.variant() === 'user'
      ? 'cb-user-attachments'
      : this.variant() === 'assistant'
        ? 'cb-message-attachments cb-message-attachments--assistant'
        : 'cb-message-attachments cb-message-attachments--inline'
  );

  imgSrc(part: ImagePart): string | null {
    return getImageDisplaySrc(part);
  }

  fileImgSrc(part: FilePart): string {
    return `data:${part.mimeType};base64,${part.data}`;
  }
}
