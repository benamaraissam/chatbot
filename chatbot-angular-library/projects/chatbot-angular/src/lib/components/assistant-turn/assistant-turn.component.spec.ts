import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AssistantTurnComponent } from './assistant-turn.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';
import type { Message } from '../../types';

function configure(): ComponentFixture<AssistantTurnComponent> {
  TestBed.configureTestingModule({
    imports: [AssistantTurnComponent],
    providers: [
      { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat', persist: false } },
      ChatbotService,
    ],
  });
  return TestBed.createComponent(AssistantTurnComponent);
}

function assistant(id: string, text: string, opts: { thinking?: string } = {}): Message {
  return {
    id,
    role: 'assistant',
    parts: [{ type: 'text', text }],
    thinking: opts.thinking,
  };
}

describe('AssistantTurnComponent', () => {
  it('renders the final message bubble when the turn has completed', () => {
    const fixture = configure();
    fixture.componentRef.setInput('message', assistant('m_done', 'All done.'));
    fixture.componentRef.setInput('isStreaming', false);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('cb-message-bubble')).not.toBeNull();
    expect(host.textContent).toContain('All done.');
  });

  it('renders a streaming-answer indicator while actively streaming', () => {
    const fixture = configure();
    const svc = TestBed.inject(ChatbotService);
    fixture.componentRef.setInput('message', assistant('m_live', ''));
    fixture.componentRef.setInput('isStreaming', true);
    fixture.componentRef.setInput('streamingText', 'partial...');
    // Mark this message as the one currently streaming so isActiveMessage is true.
    (svc as unknown as { _streamingMessageId: { set: (v: string | null) => void } })._streamingMessageId.set('m_live');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('cb-streaming-answer-indicator')).not.toBeNull();
  });

  it('renders a thinking indicator when the message carries thinking text', () => {
    const fixture = configure();
    fixture.componentRef.setInput(
      'message',
      assistant('m_think', 'final', { thinking: 'Let me consider...' }),
    );
    fixture.componentRef.setInput('isStreaming', false);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('cb-thinking-indicator')).not.toBeNull();
  });

  it('renders tool-call cards for tools attached to this message', () => {
    const fixture = configure();
    const svc = TestBed.inject(ChatbotService);
    svc.upsertToolCall('t_1', {
      name: 'get_weather',
      input: { city: 'Paris' },
      messageId: 'm_with_tools',
      status: 'done',
    });
    fixture.componentRef.setInput('message', assistant('m_with_tools', 'Result'));
    fixture.componentRef.setInput('isStreaming', false);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('cb-tool-call-card')).not.toBeNull();
    expect(host.textContent).toContain('Get Weather');
  });
});
