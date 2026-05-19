import { Component, ChangeDetectionStrategy, input } from '@angular/core';

@Component({
  selector: 'cb-bot-avatar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="cb-bot-avatar-wrap">
      <div class="cb-bot-avatar">
        <!-- Bot SVG icon -->
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 8V4H8"/><rect x="3" y="8" width="18" height="12" rx="2"/><path d="M9 12v4"/><path d="M15 12v4"/><circle cx="12" cy="3" r="1"/>
        </svg>
      </div>
      @if (loading()) {
        <div class="cb-bot-loading">
          <span class="cb-bot-loading-dots" aria-label="Thinking">
            <span></span><span></span><span></span>
          </span>
        </div>
      }
    </div>
  `,
})
export class BotAvatarComponent {
  readonly loading = input(false);
}
