import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FloatingButtonComponent } from './floating-button.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';

describe('FloatingButtonComponent', () => {
  let fixture: ComponentFixture<FloatingButtonComponent>;
  let svc: ChatbotService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FloatingButtonComponent],
      providers: [
        { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat', persist: false } },
        ChatbotService,
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(FloatingButtonComponent);
    svc = TestBed.inject(ChatbotService);
    fixture.detectChanges();
  });

  it('renders the FAB while the chat is closed', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('button.cb-fab')).not.toBeNull();
  });

  it('hides the FAB when the chat is open', () => {
    svc.setOpen(true);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('button.cb-fab')).toBeNull();
  });

  it('opens the chat when the FAB is clicked', () => {
    const host: HTMLElement = fixture.nativeElement;
    const btn = host.querySelector('button.cb-fab') as HTMLButtonElement;
    btn.click();
    fixture.detectChanges();
    expect(svc.isOpen()).toBeTrue();
  });
});
