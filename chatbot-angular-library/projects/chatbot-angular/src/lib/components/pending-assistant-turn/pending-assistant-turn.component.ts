import { Component, ChangeDetectionStrategy } from '@angular/core';
import { BotAvatarComponent } from '../bot-avatar/bot-avatar.component';

@Component({
  selector: 'cb-pending-assistant-turn',
  standalone: true,
  imports: [BotAvatarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="cb-assistant-turn">
      <cb-bot-avatar [loading]="true" class="cb-assistant-turn-avatar" />
    </div>
  `,
})
export class PendingAssistantTurnComponent {}
