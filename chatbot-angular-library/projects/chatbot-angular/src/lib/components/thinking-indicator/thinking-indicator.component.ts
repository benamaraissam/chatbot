import { Component, ChangeDetectionStrategy, input, signal, computed, effect, ElementRef, ViewChild } from '@angular/core';
import { StreamingCursorComponent } from '../streaming-cursor/streaming-cursor.component';

@Component({
  selector: 'cb-thinking-indicator',
  standalone: true,
  imports: [StreamingCursorComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (hasText() || isStreaming()) {
      <div [class]="'cb-thinking ' + (expanded() ? 'cb-thinking--expanded' : 'cb-thinking--collapsed')" role="region" aria-label="Reasoning trace">
        <button
          type="button"
          class="cb-thinking-header"
          (click)="hasText() && toggle()"
          [attr.aria-expanded]="expanded()"
          [disabled]="!hasText()"
        >
          <!-- Brain icon -->
          <svg class="cb-thinking-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/>
            <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/>
          </svg>
          <span class="cb-thinking-label">Thinking</span>
          @if (isStreaming() && !hasText()) {
            <span class="cb-thinking-dots" aria-hidden="true">
              <span></span><span></span><span></span>
            </span>
          }
          @if (!expanded() && hasText()) {
            <span class="cb-thinking-preview">{{ preview() }}</span>
          }
          @if (hasText()) {
            <svg class="cb-thinking-chevron" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>
          }
        </button>
        @if (expanded()) {
          <div #body class="cb-thinking-body" [attr.aria-live]="isStreaming() ? 'polite' : 'off'">
            @if (hasText()) {
              <p class="cb-thinking-text">
                {{ text() }}
                @if (isStreaming()) { <cb-streaming-cursor /> }
              </p>
            } @else {
              <p class="cb-thinking-text cb-thinking-text--placeholder">Reasoning…</p>
            }
          </div>
        }
      </div>
    }
  `,
})
export class ThinkingIndicatorComponent {
  readonly text = input('');
  readonly isStreaming = input(false);

  readonly expanded = signal(false);
  readonly hasText = computed(() => this.text().trim().length > 0);

  @ViewChild('body') bodyEl?: ElementRef<HTMLDivElement>;

  constructor() {
    // Expand while streaming; collapse to preview when done
    effect(() => {
      if (this.isStreaming()) {
        this.expanded.set(true);
      } else if (this.hasText()) {
        this.expanded.set(false);
      }
    }, { allowSignalWrites: true });
    effect(() => {
      if (this.isStreaming() && this.expanded() && this.text()) {
        requestAnimationFrame(() => {
          if (this.bodyEl?.nativeElement) {
            this.bodyEl.nativeElement.scrollTop = this.bodyEl.nativeElement.scrollHeight;
          }
        });
      }
    });
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
