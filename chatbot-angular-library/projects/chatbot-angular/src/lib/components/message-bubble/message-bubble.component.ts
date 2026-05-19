import { Component, ChangeDetectionStrategy, input, computed } from '@angular/core';
import { Message } from '../../types';
import { getMessageText, isImageLikePart, isFilePart } from '../../utils/message-parts';
import { StreamingCursorComponent } from '../streaming-cursor/streaming-cursor.component';
import { MarkdownMessageComponent } from '../markdown-message/markdown-message.component';
import { MessageAttachmentsComponent } from '../message-attachments/message-attachments.component';
import { CopyButtonComponent } from '../copy-button/copy-button.component';

const IMAGE_ONLY_DEFAULT_PROMPT = 'What is in this image?';

@Component({
  selector: 'cb-message-bubble',
  standalone: true,
  imports: [StreamingCursorComponent, MarkdownMessageComponent, MessageAttachmentsComponent, CopyButtonComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (isUser()) {
      <div class="cb-flex cb-flex-col cb-items-end cb-gap-1.5 cb-px-0.5">
        @if (hasAttachments()) {
          <cb-message-attachments [parts]="message().parts" variant="user" />
        }
        @if (showUserText()) {
          <div class="cb-user-bubble cb-max-w-[85%]">
            <p class="cb-whitespace-pre-wrap cb-break-words">{{ text() }}</p>
          </div>
        }
        @if (canCopy() && showUserText()) {
          <cb-copy-button [text]="text()" ariaLabel="Copy message" [inline]="true" />
        }
      </div>
    } @else {
      <div [class]="'cb-assistant-message ' + (embedded() ? 'cb-w-full' : 'cb-max-w-full')">
        <div class="cb-assistant-bubble">
          @if (showPlainStream()) {
            <p class="cb-whitespace-pre-wrap cb-text-[13px] cb-leading-[1.55] cb-text-cb-text">
              {{ text() }}<cb-streaming-cursor />
            </p>
          } @else if (showMarkdown()) {
            <cb-markdown-message [content]="text()" />
          } @else {
            <p class="cb-text-[13px] cb-text-cb-muted">…</p>
          }
        </div>
        @if (hasAssistantFiles() && !isStreaming()) {
          <cb-message-attachments [parts]="message().parts" variant="assistant" />
        }
        @if (canCopy()) {
          <div class="cb-message-actions">
            <cb-copy-button [text]="text()" ariaLabel="Copy response" />
          </div>
        }
      </div>
    }
  `,
})
export class MessageBubbleComponent {
  readonly message = input.required<Message>();
  readonly streamingText = input<string | undefined>(undefined);
  readonly isStreaming = input(false);
  readonly embedded = input(false);

  readonly isUser = computed(() => this.message().role === 'user');

  readonly text = computed(() => {
    if (this.isStreaming() && this.streamingText() !== undefined) return this.streamingText()!;
    return getMessageText(this.message());
  });

  readonly showMarkdown = computed(() => !this.isUser() && !this.isStreaming() && this.text().trim().length > 0);
  readonly showPlainStream = computed(() => !this.isUser() && this.isStreaming());
  readonly canCopy = computed(() => !this.isStreaming() && this.text().trim().length > 0);

  readonly hasAttachments = computed(() =>
    this.message().parts.some(p => isImageLikePart(p) || isFilePart(p))
  );
  readonly hasAssistantFiles = computed(() =>
    !this.isUser() && this.message().parts.some(p => isFilePart(p))
  );
  readonly showUserText = computed(() => {
    const t = this.text();
    return Boolean(t) && !(t === IMAGE_ONLY_DEFAULT_PROMPT && this.hasAttachments());
  });
}
