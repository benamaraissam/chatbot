import {
  Component,
  ChangeDetectionStrategy,
  inject,
  viewChild,
  ElementRef,
  effect,
  computed,
  AfterViewInit,
} from '@angular/core';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';
import { AssistantTurnComponent } from '../assistant-turn/assistant-turn.component';
import { MessageBubbleComponent } from '../message-bubble/message-bubble.component';
import { PendingAssistantTurnComponent } from '../pending-assistant-turn/pending-assistant-turn.component';

const DEFAULT_SUGGESTIONS = [
  'thinking demo',
  'weather in Tokyo',
  'full demo',
  'send approval email',
  'error demo',
  'markdown demo',
];

@Component({
  selector: 'cb-message-list',
  standalone: true,
  imports: [AssistantTurnComponent, MessageBubbleComponent, PendingAssistantTurnComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  /* Make this host element a proper flex child so the panel's flex layout
     keeps the header + input fixed and only this region scrolls. */
  host: { style: 'flex: 1; min-height: 0; overflow-y: auto; display: block;' },
  template: `
    <div class="cb-flex-1 cb-overflow-y-auto cb-bg-cb-bg cb-px-3 cb-py-3">
      @if (chatbot.messages().length === 0) {
        <div class="cb-flex cb-flex-col cb-items-center cb-justify-center cb-py-8 cb-gap-3">
          <!-- Sparkles icon -->
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="cb-text-cb-primary" aria-hidden="true">
            <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z"/>
            <path d="M5 3l.75 2.25L8 6l-2.25.75L5 9l-.75-2.25L2 6l2.25-.75z"/>
            <path d="M19 15l.75 2.25L22 18l-2.25.75L19 21l-.75-2.25L16 18l2.25-.75z"/>
          </svg>
          <p class="cb-text-cb-muted cb-text-center" style="font-size: 0.875rem;">
            How can I help you today?
          </p>
          @if (suggestions().length > 0) {
            <div class="cb-flex cb-flex-col cb-gap-1" style="width: 100%; max-width: 320px;">
              @for (s of suggestions(); track s) {
                <button
                  type="button"
                  class="cb-btn-ghost"
                  style="width: 100%; height: auto; padding: 0.5rem 0.75rem; border-radius: 0.75rem; font-size: 0.8125rem; justify-content: flex-start; text-align: left;"
                  (click)="chatbot.sendMessage(s)"
                >
                  {{ s }}
                </button>
              }
            </div>
          }
        </div>
      } @else {
        <div class="cb-flex cb-flex-col cb-gap-3">
          <span class="cb-sr-only" aria-live="polite" aria-atomic="false">
            @if (chatbot.isStreaming()) { Generating response… }
          </span>
          @for (message of chatbot.messages(); track message.id) {
            @if (message.role === 'assistant') {
              <cb-assistant-turn
                [message]="message"
                [isStreaming]="chatbot.isStreaming() && chatbot.streamingMessageId() === message.id"
                [streamingText]="chatbot.streamingMessageId() === message.id ? chatbot.streamingText() : undefined"
              />
            } @else if (message.role === 'user') {
              <cb-message-bubble
                [message]="message"
                [isStreaming]="false"
                [embedded]="false"
              />
            }
          }
          @if (chatbot.isAwaitingReply() && !chatbot.streamingMessageId()) {
            <cb-pending-assistant-turn />
          }
          @if (chatbot.error()) {
            <p
              class="cb-mt-2 cb-rounded-lg cb-border cb-p-3"
              style="font-size: 0.8125rem; color: var(--cb-error-text); background: var(--cb-error-bg); border-color: var(--cb-error-border);"
              role="alert"
            >
              {{ chatbot.error() }}
            </p>
          }
        </div>
      }
      <div #bottom aria-hidden="true"></div>
    </div>
  `,
})
export class MessageListComponent implements AfterViewInit {
  readonly chatbot = inject(ChatbotService);
  private readonly config = inject(CHATBOT_CONFIG);

  private readonly bottomRef = viewChild<ElementRef<HTMLDivElement>>('bottom');

  readonly suggestions = computed(() =>
    this.config.suggestions?.length ? this.config.suggestions : DEFAULT_SUGGESTIONS
  );

  constructor() {
    effect(() => {
      // Track signals that should trigger scroll
      this.chatbot.messages();
      this.chatbot.streamingText();
      this.chatbot.isAwaitingReply();
      // Scroll after Angular has updated the DOM
      queueMicrotask(() => this.scrollToBottom());
    });
  }

  ngAfterViewInit(): void {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    this.bottomRef()?.nativeElement.scrollIntoView({ block: 'end' });
  }
}
