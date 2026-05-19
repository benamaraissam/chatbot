import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { ChatbotService } from '../../services/chatbot.service';

@Component({
  selector: 'cb-floating-button',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (!chatbot.isOpen()) {
      <button
        type="button"
        class="cb-fab"
        (click)="chatbot.setOpen(true)"
        aria-label="Open chat"
      >
        <!-- MessageSquare icon -->
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="cb-sr-only">Open chat</span>
      </button>
    }
  `,
})
export class FloatingButtonComponent {
  readonly chatbot = inject(ChatbotService);
}
