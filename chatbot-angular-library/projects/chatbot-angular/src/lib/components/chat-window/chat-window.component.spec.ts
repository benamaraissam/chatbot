import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ChatWindowComponent } from './chat-window.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';

describe('ChatWindowComponent', () => {
  let fixture: ComponentFixture<ChatWindowComponent>;
  let svc: ChatbotService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatWindowComponent],
      providers: [
        { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat', persist: false, theme: 'light' } },
        ChatbotService,
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ChatWindowComponent);
    svc = TestBed.inject(ChatbotService);
  });

  it('renders nothing meaningful when the chat is closed', () => {
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    // Floating mode and closed → no .cb-chat-shell visible.
    expect(host.querySelector('.cb-chat-shell')).toBeNull();
  });

  it('renders the chat shell when the chat is open', () => {
    svc.setOpen(true);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-chat-shell')).not.toBeNull();
  });

  it('renders the embedded layout when embedded input is true', () => {
    fixture.componentRef.setInput('embedded', true);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    // Embedded mode is always rendered (no toggle gate).
    expect(host.querySelector('.cb-chat-shell--embedded')).not.toBeNull();
  });
});
