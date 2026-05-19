import { Component, ChangeDetectionStrategy, input, computed, inject } from '@angular/core';
import { Message } from '../../types';
import { ChatbotService } from '../../services/chatbot.service';
import { getToolsForMessage } from '../../utils/thread';
import { getMessageText } from '../../utils/message-parts';
import { BotAvatarComponent } from '../bot-avatar/bot-avatar.component';
import { ThinkingIndicatorComponent } from '../thinking-indicator/thinking-indicator.component';
import { StreamingAnswerIndicatorComponent } from '../streaming-answer-indicator/streaming-answer-indicator.component';
import { ToolCallCardComponent } from '../tool-call-card/tool-call-card.component';
import { MessageBubbleComponent } from '../message-bubble/message-bubble.component';

@Component({
  selector: 'cb-assistant-turn',
  standalone: true,
  imports: [
    BotAvatarComponent,
    ThinkingIndicatorComponent,
    StreamingAnswerIndicatorComponent,
    ToolCallCardComponent,
    MessageBubbleComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="cb-assistant-turn">
      <cb-bot-avatar [loading]="showAvatarLoading()" class="cb-assistant-turn-avatar" />
      <div class="cb-assistant-turn-body">

        <!-- 1. Thinking trace (while thinking or after, collapsed to preview) -->
        @if (showThinkingTrace()) {
          <cb-thinking-indicator [text]="thinkingText()" [isStreaming]="isThinkingLive()" />
        }

        <!-- 2. Response accordion while the message is actively streaming
             (shown above tool cards, same as React — empty during tool exec,
              fills with text once tools complete and model writes its answer) -->
        @if (showStreamingAnswer()) {
          <cb-streaming-answer-indicator
            [text]="streamingAnswerText()"
            [isStreaming]="true"
          />
        }

        <!-- 3. Tool call cards -->
        @if (tools().length > 0) {
          <div class="cb-tool-stack">
            @for (tool of tools(); track tool.id) {
              <cb-tool-call-card [tool]="tool" />
            }
          </div>
        }

        <!-- 4. Final rendered answer (only after streaming is fully done) -->
        @if (showAnswer()) {
          <cb-message-bubble [message]="message()" [isStreaming]="false" [embedded]="true" />
        }

      </div>
    </div>
  `,
})
export class AssistantTurnComponent {
  readonly message = input.required<Message>();
  readonly isStreaming = input(false);
  readonly streamingText = input<string | undefined>(undefined);

  private readonly chatbot = inject(ChatbotService);

  readonly tools = computed(() =>
    getToolsForMessage(this.chatbot.toolCalls(), this.message().id)
  );

  readonly isActiveMessage = computed(() =>
    this.isStreaming() && this.message().id === this.chatbot.streamingMessageId()
  );

  readonly streamingAnswerText = computed(() =>
    this.isActiveMessage() && this.streamingText() !== undefined ? this.streamingText()! : ''
  );

  readonly bufferedAnswer = computed(() => this.streamingAnswerText().trim());

  readonly thinkingText = computed(() =>
    this.isActiveMessage()
      ? this.chatbot.streamingThinkingText() || this.message().thinking || ''
      : this.message().thinking || ''
  );

  readonly isThinkingLive = computed(() =>
    this.isActiveMessage() && !this.bufferedAnswer() && Boolean(this.chatbot.streamingThinkingText())
  );

  readonly showThinkingTrace = computed(() =>
    Boolean(this.thinkingText().trim()) || this.isThinkingLive()
  );

  readonly showStreamingAnswer = computed(() =>
    this.isActiveMessage() && !this.isThinkingLive()
  );

  readonly showAnswer = computed(() =>
    !this.isActiveMessage() && Boolean(getMessageText(this.message()).trim())
  );

  readonly showAvatarLoading = computed(() =>
    this.isActiveMessage() &&
    !this.thinkingText().trim() &&
    !this.bufferedAnswer() &&
    this.tools().length === 0
  );
}
