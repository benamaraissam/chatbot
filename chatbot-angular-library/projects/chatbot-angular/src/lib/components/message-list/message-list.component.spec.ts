import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MessageListComponent } from './message-list.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';

describe('MessageListComponent', () => {
  let fixture: ComponentFixture<MessageListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MessageListComponent],
      providers: [
        {
          provide: CHATBOT_CONFIG,
          useValue: {
            endpoint: '/api/chat',
            persist: false,
            suggestions: ['Hello', 'Help me'],
          },
        },
        ChatbotService,
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(MessageListComponent);
    fixture.detectChanges();
  });

  it('renders a scrollable message list region', () => {
    const host: HTMLElement = fixture.nativeElement;
    // The list always renders its outer wrapper; the inner content varies.
    expect(host.firstElementChild).not.toBeNull();
  });

  it('renders suggestion buttons in the empty state', () => {
    const host: HTMLElement = fixture.nativeElement;
    // Suggestions render as buttons in the empty state placeholder.
    const buttons = host.querySelectorAll('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});
