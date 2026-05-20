import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PendingAssistantTurnComponent } from './pending-assistant-turn.component';

describe('PendingAssistantTurnComponent', () => {
  let fixture: ComponentFixture<PendingAssistantTurnComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PendingAssistantTurnComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(PendingAssistantTurnComponent);
    fixture.detectChanges();
  });

  it('renders the assistant-turn wrapper with a loading avatar', () => {
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('.cb-assistant-turn')).not.toBeNull();
    expect(host.querySelector('.cb-bot-loading')).not.toBeNull();
  });
});
