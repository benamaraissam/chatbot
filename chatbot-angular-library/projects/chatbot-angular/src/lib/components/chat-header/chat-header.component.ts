import { Component, ChangeDetectionStrategy, inject, input, computed } from '@angular/core';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';
import { BotAvatarComponent } from '../bot-avatar/bot-avatar.component';

@Component({
  selector: 'cb-chat-header',
  standalone: true,
  imports: [BotAvatarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { style: 'flex-shrink: 0;' },
  template: `
    <header class="cb-header">
      <cb-bot-avatar [loading]="false" class="cb-header-avatar" />
      <div class="cb-header-text">
        <h2 class="cb-header-title">{{ title() }}</h2>
        <p class="cb-header-subtitle">
          <span class="cb-header-status-dot" aria-hidden="true"></span>
          <span>Online</span>
        </p>
      </div>
      <div class="cb-header-toolbar" role="toolbar" aria-label="Chat controls">
        @if (config.allowThemeToggle) {
          <button
            type="button"
            class="cb-btn-ghost"
            [attr.aria-label]="chatbot.resolvedTheme() === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'"
            (click)="toggleTheme()"
          >
            @if (chatbot.resolvedTheme() === 'dark') {
              <!-- Sun icon -->
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            } @else {
              <!-- Moon icon -->
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            }
          </button>
        }
        <button
          type="button"
          class="cb-btn-ghost cb-btn-ghost-danger"
          aria-label="Clear conversation"
          (click)="chatbot.clearMessages()"
        >
          <!-- Trash icon -->
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14H6L5 6"/>
            <path d="M10 11v6"/>
            <path d="M14 11v6"/>
            <path d="M9 6V4h6v2"/>
          </svg>
        </button>
        @if (!embedded()) {
          <button
            type="button"
            class="cb-btn-ghost cb-btn-ghost-close"
            aria-label="Close chat"
            (click)="chatbot.setOpen(false)"
          >
            <!-- X icon -->
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        }
      </div>
    </header>
  `,
})
export class ChatHeaderComponent {
  readonly embedded = input(false);

  readonly chatbot = inject(ChatbotService);
  readonly config = inject(CHATBOT_CONFIG);

  readonly title = computed(() => this.config.title ?? 'Assistant');

  toggleTheme(): void {
    const next = this.chatbot.resolvedTheme() === 'dark' ? 'light' : 'dark';
    this.chatbot.setTheme(next);
  }
}
