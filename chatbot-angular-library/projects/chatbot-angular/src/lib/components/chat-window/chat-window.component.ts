import {
  Component,
  ChangeDetectionStrategy,
  inject,
  input,
  computed,
  effect,
} from '@angular/core';
import { ChatbotService } from '../../services/chatbot.service';
import { ChatHeaderComponent } from '../chat-header/chat-header.component';
import { MessageListComponent } from '../message-list/message-list.component';
import { ChatInputComponent } from '../chat-input/chat-input.component';
import { buildPrimaryColorStyle } from '../../utils/primaryColor';

@Component({
  selector: 'cb-chat-window',
  standalone: true,
  imports: [ChatHeaderComponent, MessageListComponent, ChatInputComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (embedded()) {
      <!-- Embedded mode -->
      <div
        [class]="'cb-root cb-root--block cb-chat-shell cb-chat-shell--embedded' + (chatbot.embeddedPanelCollapsed() ? ' cb-chat-shell--collapsed' : '')"
        [attr.data-cb-theme]="chatbot.resolvedTheme()"
        [attr.data-cb-panel-collapsed]="chatbot.embeddedPanelCollapsed() ? 'true' : null"
        [style]="primaryColorStyle()"
      >
        @if (canCollapse()) {
          <button
            type="button"
            [class]="'cb-panel-width-toggle' + (chatbot.embeddedPanelCollapsed() ? ' cb-panel-width-toggle--collapsed-pin' : '')"
            [attr.aria-pressed]="chatbot.embeddedPanelCollapsed()"
            [attr.aria-label]="chatbot.embeddedPanelCollapsed() ? 'Open chat panel' : 'Collapse chat panel'"
            (click)="chatbot.toggleEmbeddedPanelCollapsed()"
          >
            <span class="cb-panel-width-toggle-icon" aria-hidden="true">
              @if (chatbot.embeddedPanelCollapsed()) {
                <!-- Chevron left (open) -->
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
              } @else {
                <!-- Chevron right (collapse) -->
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              }
            </span>
          </button>
        }
        @if (!chatbot.embeddedPanelCollapsed()) {
          <div class="cb-chat-frame">
            <div class="cb-chat-panel">
              <cb-chat-header [embedded]="true" />
              <cb-message-list />
              <cb-chat-input />
            </div>
          </div>
        }
      </div>
    } @else {
      <!-- Overlay mode -->
      @if (chatbot.isOpen()) {
        <div
          class="cb-root cb-root--overlay"
          [attr.data-cb-theme]="chatbot.resolvedTheme()"
          [style]="primaryColorStyle()"
        >
          <!-- Backdrop -->
          <div
            class="cb-fixed cb-inset-0 cb-z-[9998] md:cb-bg-[var(--cb-backdrop)]"
            aria-hidden="true"
            (click)="chatbot.setOpen(false)"
          ></div>
          <!-- Chat shell -->
          <div class="cb-chat-shell">
            <div [class]="'cb-chat-frame' + (chatbot.panelWide() ? ' cb-chat-frame--wide' : '')">
              <!-- Wide toggle -->
              <button
                type="button"
                class="cb-panel-width-toggle"
                [attr.aria-pressed]="chatbot.panelWide()"
                [attr.aria-label]="chatbot.panelWide() ? 'Narrow panel' : 'Widen panel'"
                (click)="chatbot.togglePanelWide()"
              >
                <span class="cb-panel-width-toggle-icon" aria-hidden="true">
                  @if (chatbot.panelWide()) {
                    <!-- Chevron right (narrow) -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  } @else {
                    <!-- Chevron left (widen) -->
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="15 18 9 12 15 6"/>
                    </svg>
                  }
                </span>
              </button>
              <div class="cb-chat-panel">
                <cb-chat-header [embedded]="false" />
                <cb-message-list />
                <cb-chat-input />
              </div>
            </div>
          </div>
        </div>
      }
    }
  `,
})
export class ChatWindowComponent {
  readonly embedded = input(false);
  readonly collapsible = input<boolean | undefined>(undefined);

  readonly chatbot = inject(ChatbotService);

  readonly canCollapse = computed(() => this.embedded() && (this.collapsible() ?? true));

  readonly primaryColorStyle = computed(() => {
    const color = this.chatbot.primaryColor();
    const theme = this.chatbot.resolvedTheme();
    return color ? buildPrimaryColorStyle(color, theme) : {};
  });

  constructor() {
    effect(() => {
      if (this.embedded()) {
        this.chatbot.setEmbeddedPanelCollapsed(false);
      }
    }, { allowSignalWrites: true });
  }
}
