import { Component, ChangeDetectionStrategy, input } from '@angular/core';
import { PendingAttachment } from '../../utils/attachments';
import { formatFileSize } from '../../utils/message-parts';

@Component({
  selector: 'cb-composer-attachments',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (items().length > 0) {
      <div class="cb-composer-attachments">
        @for (item of items(); track item.id) {
          @if (isImage(item)) {
            <div class="cb-composer-attachment cb-composer-attachment--image">
              <img
                [src]="item.previewUrl || ''"
                [alt]="item.file.name"
                class="cb-composer-attachment-thumb"
              />
              <div class="cb-composer-attachment-meta cb-composer-attachment-meta--image">
                <span class="cb-composer-attachment-name">{{ item.file.name }}</span>
                <span class="cb-composer-attachment-size">{{ fileSize(item.file.size) }}</span>
              </div>
              <button
                type="button"
                class="cb-composer-attachment-remove"
                [attr.aria-label]="'Remove ' + item.file.name"
                (click)="remove(item.id)"
              >
                <!-- X icon -->
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          } @else {
            <div class="cb-composer-attachment">
              <div class="cb-composer-attachment-file">
                <!-- File icon -->
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div class="cb-composer-attachment-meta">
                <span class="cb-composer-attachment-name">{{ item.file.name }}</span>
                <span class="cb-composer-attachment-size">{{ fileSize(item.file.size) }}</span>
              </div>
              <button
                type="button"
                class="cb-composer-attachment-remove"
                [attr.aria-label]="'Remove ' + item.file.name"
                (click)="remove(item.id)"
              >
                <!-- X icon -->
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          }
        }
      </div>
    }
  `,
})
export class ComposerAttachmentsComponent {
  readonly items = input<PendingAttachment[]>([]);
  readonly onRemove = input<(id: string) => void>(() => () => {});

  isImage(item: PendingAttachment): boolean {
    return item.file.type.startsWith('image/');
  }

  fileSize(bytes: number): string {
    return formatFileSize(bytes);
  }

  remove(id: string): void {
    this.onRemove()(id);
  }
}
