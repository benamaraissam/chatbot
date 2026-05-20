import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BotAvatarComponent } from './bot-avatar.component';

describe('BotAvatarComponent', () => {
  let fixture: ComponentFixture<BotAvatarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BotAvatarComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(BotAvatarComponent);
    fixture.detectChanges();
  });

  it('renders the avatar wrapper and SVG icon', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-bot-avatar-wrap')).not.toBeNull();
    expect(host.querySelector('.cb-bot-avatar svg')).not.toBeNull();
  });

  it('does not render the loading indicator by default', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-bot-loading')).toBeNull();
  });

  it('renders the loading indicator when loading is true', () => {
    fixture.componentRef.setInput('loading', true);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-bot-loading')).not.toBeNull();
  });
});
