import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StreamingCursorComponent } from './streaming-cursor.component';

describe('StreamingCursorComponent', () => {
  let fixture: ComponentFixture<StreamingCursorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StreamingCursorComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(StreamingCursorComponent);
    fixture.detectChanges();
  });

  it('renders a streaming cursor span', () => {
    const host: HTMLElement = fixture.nativeElement;
    const span = host.querySelector('.cb-streaming-cursor');
    expect(span).not.toBeNull();
    expect(span!.getAttribute('aria-hidden')).toBe('true');
  });
});
