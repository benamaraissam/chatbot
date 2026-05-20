import { TestBed } from '@angular/core/testing';
import { CHATBOT_CONFIG, ChatbotConfig } from '../tokens/chatbot-config.token';
import { ChatbotService } from './chatbot.service';

function setup(config: Partial<ChatbotConfig> = {}): ChatbotService {
  TestBed.configureTestingModule({
    providers: [
      {
        provide: CHATBOT_CONFIG,
        useValue: { endpoint: '/api/chat', persist: false, ...config },
      },
      ChatbotService,
    ],
  });
  return TestBed.inject(ChatbotService);
}

describe('ChatbotService — advanced flows', () => {
  it('toggleOpen flips isOpen', () => {
    const svc = setup();
    expect(svc.isOpen()).toBeFalse();
    svc.toggleOpen();
    expect(svc.isOpen()).toBeTrue();
    svc.toggleOpen();
    expect(svc.isOpen()).toBeFalse();
  });

  it('setOpen drives isOpen directly', () => {
    const svc = setup();
    svc.setOpen(true);
    expect(svc.isOpen()).toBeTrue();
    svc.setOpen(false);
    expect(svc.isOpen()).toBeFalse();
  });

  it('setTheme updates the resolved theme for explicit modes', () => {
    const svc = setup();
    svc.setTheme('dark');
    expect(svc.theme()).toBe('dark');
    expect(svc.resolvedTheme()).toBe('dark');
    svc.setTheme('light');
    expect(svc.resolvedTheme()).toBe('light');
  });

  it('clearMessages keeps the conversation empty when invoked on a clean state', () => {
    const svc = setup();
    expect(svc.messages()).toEqual([]);
    // Should not throw and must leave the conversation empty.
    svc.clearMessages();
    expect(svc.messages()).toEqual([]);
  });

  it('togglePanelWide flips the wide-panel flag', () => {
    const svc = setup();
    expect(svc.panelWide()).toBeFalse();
    svc.togglePanelWide();
    expect(svc.panelWide()).toBeTrue();
  });

  it('setEmbeddedPanelCollapsed drives the collapsed flag directly', () => {
    const svc = setup();
    expect(svc.embeddedPanelCollapsed()).toBeFalse();
    svc.setEmbeddedPanelCollapsed(true);
    expect(svc.embeddedPanelCollapsed()).toBeTrue();
  });
});
