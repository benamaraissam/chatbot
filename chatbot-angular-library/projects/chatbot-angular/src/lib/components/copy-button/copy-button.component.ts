import { Component, ChangeDetectionStrategy, input, signal } from '@angular/core';

@Component({
  selector: 'cb-copy-button',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      type="button"
      [class]="'cb-copy-btn' + (copied() ? ' cb-copy-btn--copied' : '') + (inline() ? ' cb-copy-btn--inline' : '')"
      (click)="copy()"
      [attr.aria-label]="ariaLabel() || 'Copy'"
    >
      @if (copied()) {
        <!-- Check icon -->
        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
        Copied
      } @else {
        <!-- Copy icon -->
        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        Copy
      }
    </button>
  `,
})
export class CopyButtonComponent {
  readonly text = input('');
  readonly ariaLabel = input('Copy');
  readonly inline = input(false);
  readonly copied = signal(false);

  async copy(): Promise<void> {
    if (!this.text()) return;
    try {
      await navigator.clipboard.writeText(this.text());
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    } catch {
      // clipboard unavailable
    }
  }
}
