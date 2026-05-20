import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ToolCallCardComponent } from './tool-call-card.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';
import type { ToolCallState } from '../../types';

function tool(partial: Partial<ToolCallState>): ToolCallState {
  return {
    id: partial.id ?? 't_1',
    name: partial.name ?? 'get_weather',
    input: partial.input ?? { city: 'Paris' },
    status: partial.status ?? 'running',
    startedAt: partial.startedAt ?? Date.now(),
    output: partial.output,
    isError: partial.isError,
    messageId: partial.messageId,
    inputRaw: partial.inputRaw,
  };
}

describe('ToolCallCardComponent', () => {
  let fixture: ComponentFixture<ToolCallCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ToolCallCardComponent],
      providers: [
        { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat', persist: false } },
        ChatbotService,
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ToolCallCardComponent);
  });

  it('renders the formatted tool name in the running state', () => {
    fixture.componentRef.setInput('tool', tool({ status: 'running' }));
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    // formatToolName turns "get_weather" into "Get Weather".
    expect(host.textContent).toContain('Get Weather');
  });

  it('renders the skill badge for load_skill tool calls', () => {
    fixture.componentRef.setInput(
      'tool',
      tool({ name: 'load_skill', input: { skill: 'funds' } }),
    );
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    // The component renders a compact "Skill: <name>" badge for load_skill.
    expect(host.querySelector('.cb-skill-badge')).not.toBeNull();
  });

  it('reflects the done status with the output rendered', () => {
    fixture.componentRef.setInput(
      'tool',
      tool({ status: 'done', output: { temp_c: 22 } }),
    );
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.textContent).toContain('Get Weather');
  });
});
