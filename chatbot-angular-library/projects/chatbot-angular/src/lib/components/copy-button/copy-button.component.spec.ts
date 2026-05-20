import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { CopyButtonComponent } from './copy-button.component';

describe('CopyButtonComponent', () => {
  let fixture: ComponentFixture<CopyButtonComponent>;
  let writeText: jasmine.Spy<(text: string) => Promise<void>>;

  beforeEach(async () => {
    writeText = jasmine
      .createSpy<(text: string) => Promise<void>>('writeText')
      .and.resolveTo(undefined);
    // jsdom-style browser test runner (Karma + Chrome) exposes navigator.clipboard,
    // but we stub it to capture invocations and keep tests hermetic.
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });

    await TestBed.configureTestingModule({
      imports: [CopyButtonComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(CopyButtonComponent);
    fixture.detectChanges();
  });

  it('renders a button with the default "Copy" label', () => {
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(btn).not.toBeNull();
    expect(btn.textContent).toContain('Copy');
  });

  it('does not call the clipboard API when text input is empty', async () => {
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    btn.click();
    await fixture.whenStable();
    expect(writeText).not.toHaveBeenCalled();
  });

  it('writes the configured text to the clipboard on click', async () => {
    fixture.componentRef.setInput('text', 'hello world');
    fixture.detectChanges();

    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    btn.click();
    await fixture.whenStable();

    expect(writeText).toHaveBeenCalledWith('hello world');
  });

  it('flips to the "Copied" state after a successful copy', fakeAsync(() => {
    fixture.componentRef.setInput('text', 'hi');
    fixture.detectChanges();

    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    btn.click();
    tick(); // resolve the writeText promise
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Copied');

    // The 2-second timeout flips the state back.
    tick(2000);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Copy');
  }));

  it('honours the aria-label input', () => {
    fixture.componentRef.setInput('ariaLabel', 'Copy code');
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(btn.getAttribute('aria-label')).toBe('Copy code');
  });
});
