import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MessageBubbleComponent } from './message-bubble.component';
import type { Message } from '../../types';

function makeMessage(role: 'user' | 'assistant', text: string): Message {
  return {
    id: `m_${role}_1`,
    role,
    parts: [{ type: 'text', text }],
  };
}

describe('MessageBubbleComponent', () => {
  let fixture: ComponentFixture<MessageBubbleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MessageBubbleComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(MessageBubbleComponent);
  });

  it('renders the user bubble with the user text', () => {
    fixture.componentRef.setInput('message', makeMessage('user', 'Hi there'));
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-user-bubble')).not.toBeNull();
    expect(host.textContent).toContain('Hi there');
  });

  it('renders an assistant bubble with markdown content', () => {
    fixture.componentRef.setInput(
      'message',
      makeMessage('assistant', '**Bold** answer'),
    );
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    // Markdown rendering swaps in a <strong> for the bold text.
    expect(host.querySelector('strong')).not.toBeNull();
  });
});
