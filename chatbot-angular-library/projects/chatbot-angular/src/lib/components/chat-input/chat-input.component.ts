import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal,
  computed,
  viewChild,
  ElementRef,
} from '@angular/core';
import { MessagePart } from '../../types';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';
import {
  PendingAttachment,
  filesToAttachmentParts,
  validateAttachmentBatch,
  DEFAULT_ATTACHMENT_ACCEPT,
} from '../../utils/attachments';
import { registerDisplayUrl } from '../../utils/attachment-display';
import { createId } from '../../utils/id';
import { ComposerAttachmentsComponent } from '../composer-attachments/composer-attachments.component';

@Component({
  selector: 'cb-chat-input',
  standalone: true,
  imports: [ComposerAttachmentsComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'flex-shrink: 0;' },
  template: `
    <div class="cb-shrink-0 cb-border-t cb-border-cb-border cb-bg-cb-surface cb-p-3">

      <cb-composer-attachments
        [items]="chatbot.composerAttachments()"
        [onRemove]="removeAttachmentFn"
      />

      @if (isReadingFiles()) {
        <p class="cb-composer-attach-status" aria-live="polite">Reading file…</p>
      }
      @if (attachError()) {
        <p class="cb-composer-attach-error" role="alert">{{ attachError() }}</p>
      }

      <!-- Rounded composer shell -->
      <div class="cb-composer-shell cb-relative cb-flex cb-flex-col cb-gap-2 cb-p-2">

        <!-- Hidden file input — always in DOM so triggerFileInput() works -->
        @if (attachmentsEnabled()) {
          <input
            #fileInput
            type="file"
            class="cb-file-input-hidden"
            multiple
            [attr.accept]="attachAccept()"
            (change)="onFileChange($event)"
            tabindex="-1"
            aria-hidden="true"
          />
        }

        <!-- Horizontal row: attach | textarea | send/stop -->
        <div class="cb-flex cb-items-end cb-gap-1">

          @if (attachmentsEnabled()) {
            <button
              type="button"
              class="cb-composer-attach"
              aria-label="Attach files or images"
              [disabled]="chatbot.isStreaming() || isReadingFiles()"
              (click)="triggerFileInput()"
            >
              <!-- Paperclip -->
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
              </svg>
            </button>
          }

          <textarea
            #textarea
            class="cb-composer-textarea cb-flex-1 cb-resize-none cb-border-0 cb-bg-transparent cb-outline-none cb-text-cb-text"
            style="min-height:36px; max-height:120px; font-size:13px; line-height:1.45; padding: 0.5rem 0.25rem;"
            [placeholder]="placeholder()"
            [value]="inputText()"
            rows="1"
            [disabled]="chatbot.isStreaming()"
            (input)="onInput($event)"
            (keydown)="onKeydown($event)"
            aria-label="Message input"
          ></textarea>

          @if (chatbot.isStreaming()) {
            <button
              type="button"
              class="cb-composer-action cb-composer-action--stop"
              aria-label="Stop generating"
              (click)="chatbot.stopStreaming()"
            >
              <!-- Square / stop -->
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              </svg>
            </button>
          } @else {
            <button
              type="button"
              class="cb-composer-action cb-composer-action--send"
              aria-label="Send message"
              [disabled]="!canSend()"
              (click)="submit()"
            >
              <!-- Arrow up / send -->
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <line x1="12" y1="19" x2="12" y2="5"/>
                <polyline points="5 12 12 5 19 12"/>
              </svg>
            </button>
          }

        </div>
      </div>

      <!-- Hint line -->
      <p style="margin-top:0.5rem; text-align:center; font-size:10px; color:var(--cb-muted);">
        Enter to send · Shift+Enter for new line
        @if (attachmentsEnabled()) { · Attach images or files }
      </p>

    </div>
  `,
})
export class ChatInputComponent {
  readonly chatbot = inject(ChatbotService);
  private readonly config = inject(CHATBOT_CONFIG);

  private readonly textareaRef = viewChild<ElementRef<HTMLTextAreaElement>>('textarea');
  private readonly fileInputRef = viewChild<ElementRef<HTMLInputElement>>('fileInput');

  readonly inputText = signal('');
  readonly attachError = signal<string | null>(null);
  readonly isReadingFiles = signal(false);

  readonly canSend = computed(
    () =>
      (this.inputText().trim().length > 0 ||
        this.chatbot.composerAttachments().length > 0) &&
      !this.chatbot.isStreaming()
  );

  readonly attachmentsEnabled = computed(() => this.chatbot.attachmentsEnabled());

  readonly attachAccept = computed(
    () => this.config.attachments?.accept ?? DEFAULT_ATTACHMENT_ACCEPT
  );

  readonly placeholder = computed(() => this.config.placeholder ?? 'Message…');

  /** Stable function reference passed to ComposerAttachmentsComponent */
  readonly removeAttachmentFn = (id: string) => this.chatbot.removeComposerAttachment(id);

  onInput(event: Event): void {
    const el = event.target as HTMLTextAreaElement;
    this.inputText.set(el.value);
    this.autoResize(el);
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (this.canSend()) {
        this.submit();
      }
    }
  }

  triggerFileInput(): void {
    this.attachError.set(null);
    this.fileInputRef()?.nativeElement.click();
  }

  async onFileChange(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files ?? []);
    input.value = '';
    if (files.length === 0) return;

    const maxCount = this.config.attachments?.maxCount ?? 5;
    const maxBytes = this.config.attachments?.maxSizeBytes ?? 10 * 1024 * 1024;
    const existing = this.chatbot.composerAttachments().length;

    const validationError = validateAttachmentBatch(files, {
      maxCount: maxCount - existing,
      maxSizeBytes: maxBytes,
    });
    if (validationError) {
      this.attachError.set(validationError);
      return;
    }

    this.isReadingFiles.set(true);
    this.attachError.set(null);
    try {
      const parts = await filesToAttachmentParts(files);
      const pending: PendingAttachment[] = files.map((file, i) => {
        const part = parts[i];
        const previewUrl =
          file.type.startsWith('image/') && part && 'displayUrl' in part
            ? (part as { displayUrl?: string }).displayUrl
            : undefined;
        if (previewUrl) registerDisplayUrl(previewUrl);
        return {
          id: createId('att'),
          file,
          previewUrl,
          status: 'ready' as const,
        };
      });
      this.chatbot.addComposerAttachments(pending);
    } catch {
      this.attachError.set('Failed to read one or more files.');
    } finally {
      this.isReadingFiles.set(false);
    }
  }

  async submit(): Promise<void> {
    const text = this.inputText().trim();
    const attachments = this.chatbot.composerAttachments();

    let attachmentParts: MessagePart[] = [];
    if (attachments.length > 0) {
      try {
        attachmentParts = await filesToAttachmentParts(attachments.map(a => a.file));
      } catch {
        this.attachError.set('Failed to prepare attachments.');
        return;
      }
    }

    this.chatbot.clearComposerAttachments({ revoke: false });
    this.inputText.set('');
    const ta = this.textareaRef()?.nativeElement;
    if (ta) {
      ta.value = '';
      ta.style.height = '';
    }

    await this.chatbot.sendMessage(text, { attachmentParts });
  }

  private autoResize(el: HTMLTextAreaElement): void {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }
}
