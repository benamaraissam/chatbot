import { Component, ChangeDetectionStrategy, inject, computed } from '@angular/core';
import { FloatingButtonComponent } from '../floating-button/floating-button.component';
import { ChatWindowComponent } from '../chat-window/chat-window.component';
import { ChatbotService } from '../../services/chatbot.service';
import { buildPrimaryColorStyle } from '../../utils/primaryColor';

@Component({
  selector: 'cb-floating-chatbot',
  standalone: true,
  imports: [FloatingButtonComponent, ChatWindowComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  /**
   * Wrap everything in a .cb-root element so that CSS custom properties
   * (--cb-primary, --cb-bg, etc.) are available to both the FAB button
   * and the overlay chat window — mirroring React's ChatbotProvider div.
   *
   * Note: we do NOT use cb-root--overlay here because ChatWindowComponent
   * already renders its own overlay wrapper (position:fixed) when open.
   * This div is non-positioned (static), purely for CSS variable inheritance.
   */
  template: `
    <div
      class="cb-root"
      [attr.data-cb-theme]="chatbot.resolvedTheme()"
      [style]="primaryColorStyle()"
    >
      <cb-floating-button />
      <cb-chat-window />
    </div>
  `,
})
export class FloatingChatbotComponent {
  readonly chatbot = inject(ChatbotService);

  readonly primaryColorStyle = computed(() => {
    const color = this.chatbot.primaryColor();
    const theme = this.chatbot.resolvedTheme();
    return color ? buildPrimaryColorStyle(color, theme) : {};
  });
}
