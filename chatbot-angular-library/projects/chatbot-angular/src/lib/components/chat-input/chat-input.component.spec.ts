import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ChatInputComponent } from './chat-input.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';

describe('ChatInputComponent', () => {
  let fixture: ComponentFixture<ChatInputComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatInputComponent],
      providers: [
        {
          provide: CHATBOT_CONFIG,
          useValue: {
            endpoint: '/api/chat',
            persist: false,
            placeholder: 'Ask me something…',
          },
        },
        ChatbotService,
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ChatInputComponent);
    fixture.detectChanges();
  });

  it('renders a textarea with the configured placeholder', () => {
    const host: HTMLElement = fixture.nativeElement;
    const textarea = host.querySelector('textarea');
    expect(textarea).not.toBeNull();
    expect(textarea!.getAttribute('placeholder')).toBe('Ask me something…');
  });

  it('renders a send button that is disabled while the input is empty', () => {
    const host: HTMLElement = fixture.nativeElement;
    const send = host.querySelector(
      'button[aria-label="Send message"]',
    ) as HTMLButtonElement | null;
    expect(send).not.toBeNull();
    // Empty composer → send is disabled (canSend() is false).
    expect(send!.disabled).toBeTrue();
  });
});
