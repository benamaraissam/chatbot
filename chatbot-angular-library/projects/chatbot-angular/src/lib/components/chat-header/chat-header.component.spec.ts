import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ChatHeaderComponent } from './chat-header.component';
import { ChatbotService } from '../../services/chatbot.service';
import { CHATBOT_CONFIG } from '../../tokens/chatbot-config.token';

function configureWith(config: Record<string, unknown>) {
  TestBed.configureTestingModule({
    imports: [ChatHeaderComponent],
    providers: [
      { provide: CHATBOT_CONFIG, useValue: { endpoint: '/api/chat', persist: false, ...config } },
      ChatbotService,
    ],
  });
}

describe('ChatHeaderComponent', () => {
  it('renders the configured title', () => {
    configureWith({ title: 'My Assistant' });
    const fixture = TestBed.createComponent(ChatHeaderComponent);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-header-title')?.textContent?.trim()).toBe(
      'My Assistant',
    );
  });

  it('does not show the theme toggle when allowThemeToggle is false', () => {
    configureWith({ allowThemeToggle: false });
    const fixture = TestBed.createComponent(ChatHeaderComponent);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    // No theme toggle button rendered.
    expect(host.querySelector('.cb-btn-ghost[aria-label*="theme"]')).toBeNull();
  });

  it('renders the theme toggle when allowThemeToggle is true', () => {
    configureWith({ allowThemeToggle: true, theme: 'light' });
    const fixture = TestBed.createComponent(ChatHeaderComponent);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    const toggle = host.querySelector('button.cb-btn-ghost') as HTMLButtonElement | null;
    expect(toggle).not.toBeNull();
  });
});
