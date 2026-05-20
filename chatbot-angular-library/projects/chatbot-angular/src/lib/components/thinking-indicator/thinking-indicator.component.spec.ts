import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ThinkingIndicatorComponent } from './thinking-indicator.component';

describe('ThinkingIndicatorComponent', () => {
  let fixture: ComponentFixture<ThinkingIndicatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ThinkingIndicatorComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(ThinkingIndicatorComponent);
    fixture.componentRef.setInput('text', '');
    fixture.componentRef.setInput('isStreaming', false);
    fixture.detectChanges();
  });

  it('renders nothing when text is empty and not streaming', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-thinking')).toBeNull();
  });

  it('renders the region while streaming', () => {
    fixture.componentRef.setInput('isStreaming', true);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-thinking')).not.toBeNull();
  });

  it('renders the region when text is present', () => {
    fixture.componentRef.setInput('text', 'Some reasoning...');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-thinking')).not.toBeNull();
    expect(host.textContent).toContain('Thinking');
  });
});
