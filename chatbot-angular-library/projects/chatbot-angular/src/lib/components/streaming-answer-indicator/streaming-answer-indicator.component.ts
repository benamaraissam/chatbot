import { Component, ChangeDetectionStrategy, input, signal, computed, effect } from '@angular/core';
import { StreamingCursorComponent } from '../streaming-cursor/streaming-cursor.component';

/** Port of React's StreamingAnswerIndicator.
 *
 * Shown while the assistant message is actively streaming. Renders a
 * collapsible "Response" accordion — always collapsed by default, with a
 * preview of the streaming text and animated dots while waiting. The final
 * MessageBubble replaces this component once streaming is done.
 */
@Component({
  selector: 'cb-streaming-answer-indicator',
  standalone: true,
  imports: [StreamingCursorComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      [class]="'cb-response ' + (expanded() ? 'cb-response--expanded' : 'cb-response--collapsed')"
      role="region"
      aria-label="Response in progress"
    >
      <button
        type="button"
        class="cb-response-header"
        [disabled]="!hasText()"
        [attr.aria-expanded]="expanded()"
        (click)="hasText() && toggle()"
      >
        <!-- MessageSquare icon -->
        <svg class="cb-response-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25"
          stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>

        <span class="cb-response-label">Response</span>

        <!-- Animated dots while streaming -->
        @if (isStreaming()) {
          <span class="cb-thinking-dots" aria-hidden="true">
            <span></span><span></span><span></span>
          </span>
        }

        <!-- Preview when collapsed and has text -->
        @if (!expanded() && hasText()) {
          <span class="cb-response-preview">{{ preview() }}</span>
        }

        <!-- Chevron when expandable -->
        @if (hasText()) {
          <svg class="cb-response-chevron" xmlns="http://www.w3.org/2000/svg" width="16" height="16"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        }
      </button>

      @if (expanded() && hasText()) {
        <div class="cb-response-body" aria-live="polite">
          <p class="cb-response-text">
            {{ text() }}
            @if (isStreaming()) { <cb-streaming-cursor /> }
          </p>
        </div>
      }
    </div>
  `,
})
export class StreamingAnswerIndicatorComponent {
  readonly text = input('');
  readonly isStreaming = input(true);

  readonly expanded = signal(false);
  readonly hasText = computed(() => this.text().trim().length > 0);

  constructor() {
    // Always reset to collapsed when streaming restarts
    effect(() => {
      if (this.isStreaming()) {
        this.expanded.set(false);
      }
    }, { allowSignalWrites: true });
  }

  toggle(): void {
    if (this.hasText()) this.expanded.update(v => !v);
  }

  preview(): string {
    const oneLine = this.text().replace(/\s+/g, ' ').trim();
    const max = 72;
    return oneLine.length <= max ? oneLine : oneLine.slice(0, max) + '…';
  }
}
