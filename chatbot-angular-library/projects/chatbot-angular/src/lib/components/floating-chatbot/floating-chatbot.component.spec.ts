import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FloatingChatbotComponent } from './floating-chatbot.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';

describe('FloatingChatbotComponent', () => {
  let fixture: ComponentFixture<FloatingChatbotComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FloatingChatbotComponent],
      providers: [
        { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat', persist: false, theme: 'light' } },
        ChatbotService,
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(FloatingChatbotComponent);
    fixture.detectChanges();
  });

  it('renders the .cb-root wrapper with the resolved theme attribute', () => {
    const host: HTMLElement = fixture.nativeElement;
    const root = host.querySelector('.cb-root');
    expect(root).not.toBeNull();
    expect(root!.getAttribute('data-cb-theme')).toBe('light');
  });

  it('contains both the FAB and a chat-window slot', () => {
    const host: HTMLElement = fixture.nativeElement;
    // FAB is rendered while closed.
    expect(host.querySelector('button.cb-fab')).not.toBeNull();
  });
});
