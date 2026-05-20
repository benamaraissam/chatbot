import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MarkdownMessageComponent } from './markdown-message.component';

describe('MarkdownMessageComponent', () => {
  let fixture: ComponentFixture<MarkdownMessageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarkdownMessageComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(MarkdownMessageComponent);
  });

  it('renders bold markdown as <strong>', () => {
    fixture.componentRef.setInput('content', 'This is **important** text');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('strong')).not.toBeNull();
  });

  it('renders italic markdown as <em>', () => {
    fixture.componentRef.setInput('content', 'Mind the *gap*');
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('em')).not.toBeNull();
  });

  it('renders code blocks inside .cb-code-block wrappers', () => {
    fixture.componentRef.setInput(
      'content',
      '```python\nprint("hi")\n```',
    );
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-code-block')).not.toBeNull();
  });

  it('renders empty content without crashing', () => {
    fixture.componentRef.setInput('content', '');
    fixture.detectChanges();
    expect(fixture.nativeElement).toBeTruthy();
  });
});
