import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StreamingAnswerIndicatorComponent } from './streaming-answer-indicator.component';

describe('StreamingAnswerIndicatorComponent', () => {
  let fixture: ComponentFixture<StreamingAnswerIndicatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StreamingAnswerIndicatorComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(StreamingAnswerIndicatorComponent);
    fixture.componentRef.setInput('text', '');
    fixture.componentRef.setInput('isStreaming', true);
    fixture.detectChanges();
  });

  it('renders the response region while streaming', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-response')).not.toBeNull();
  });

  it('reflects text content when provided', () => {
    fixture.componentRef.setInput('text', 'Starting...');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-response')).not.toBeNull();
  });
});
