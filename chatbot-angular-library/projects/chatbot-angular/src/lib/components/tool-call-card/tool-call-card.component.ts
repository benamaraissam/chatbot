import { Component, ChangeDetectionStrategy, input, signal, effect, inject, computed } from '@angular/core';
import { ToolCallState } from '../../types';
import { ChatbotService } from '../../services/chatbot.service';
import { formatToolName, formatToolInput, getToolInputSummary } from '../../utils/thread';

@Component({
  selector: 'cb-tool-call-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <!-- Skill badge: compact pill for load_skill calls -->
    @if (isSkill()) {
      <div
        [class]="'cb-skill-badge' + (tool().status === 'error' ? ' cb-skill-badge--error' : '')"
        [title]="tool().status === 'error' ? 'Failed to load skill' : 'Skill &quot;' + skillName() + '&quot; loaded'"
      >
        @if (tool().status === 'running') {
          <!-- Loader spinner -->
          <svg class="cb-animate-spin" xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
        } @else if (tool().status === 'error') {
          <!-- Alert triangle -->
          <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        } @else {
          <!-- BookOpen icon -->
          <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
        }
        <span class="cb-skill-badge-label">
          {{ tool().status === 'running' ? 'Loading skill…' : 'Skill: ' + skillName() }}
        </span>
      </div>
    } @else {
      <!-- Standard tool card -->
      <article
        [class]="'cb-tool-card cb-tool-card--' + tool().status"
        [attr.data-expanded]="open() ? 'true' : 'false'"
      >
        <button type="button" class="cb-tool-card-header" (click)="toggleOpen()" [attr.aria-expanded]="open()">
          <div class="cb-tool-card-icon" aria-hidden="true">
            <!-- Zap icon -->
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <div class="cb-tool-card-meta">
            <span class="cb-tool-card-eyebrow">Tool</span>
            <span class="cb-tool-card-name">{{ displayName() }}</span>
            @if (summary() && !open()) {
              <span class="cb-tool-card-summary">{{ summary() }}</span>
            }
          </div>
          <span class="cb-tool-status-pill">
            @if (tool().status === 'running') {
              <svg class="cb-animate-spin" xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
            } @else if (tool().status === 'done') {
              <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            } @else {
              <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            }
            {{ statusLabel() }}
          </span>
          <svg class="cb-tool-chevron" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        @if (open()) {
          <div class="cb-tool-card-body">
            <div class="cb-tool-code-block">
              <div class="cb-tool-code-label"><span>Parameters</span></div>
              <pre class="cb-tool-code-content">{{ inputText() || '{}' }}</pre>
            </div>
            @if (tool().output !== undefined) {
              <div class="cb-tool-code-block">
                <div class="cb-tool-code-label"><span>{{ tool().isError ? 'Error' : 'Result' }}</span></div>
                <pre [class]="'cb-tool-code-content' + (tool().isError ? ' cb-tool-code-content--error' : '')">{{ formatOutput(tool().output) }}</pre>
              </div>
            }
            @if (tool().status === 'approval') {
              <div class="cb-tool-approval-box">
                <p class="cb-tool-approval-title">Allow this action?</p>
                <p class="cb-tool-approval-desc">The assistant wants to run <strong>{{ displayName() }}</strong>. Approve only if you trust this operation.</p>
                <div class="cb-tool-approval-actions">
                  <button type="button" class="cb-tool-btn-approve" (click)="approve()">Approve</button>
                  <button type="button" class="cb-tool-btn-deny" (click)="deny()">Deny</button>
                </div>
              </div>
            }
          </div>
        }
      </article>
    }
  `,
})
export class ToolCallCardComponent {
  readonly tool = input.required<ToolCallState>();
  private readonly chatbot = inject(ChatbotService);

  readonly open = signal(false);

  /** True when this tool call should render as a compact skill badge */
  readonly isSkill = computed(() => this.tool().name === 'load_skill');

  /** Skill name extracted from the tool input (used in the badge label).
   *  tool.input is empty ({}) during streaming — actual args live in inputRaw. */
  readonly skillName = computed(() => {
    const fromInput = this.tool().input?.['name'];
    if (typeof fromInput === 'string') return fromInput;
    const raw = this.tool().inputRaw;
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as Record<string, unknown>;
        if (typeof parsed?.['name'] === 'string') return parsed['name'];
      } catch {}
    }
    return 'skill';
  });

  readonly displayName = computed(() => formatToolName(this.tool().name));
  readonly summary = computed(() => getToolInputSummary(this.tool()));
  readonly inputText = computed(() => formatToolInput(this.tool()));
  readonly statusLabel = computed(() => {
    const map: Record<string, string> = { running: 'Running', done: 'Done', error: 'Failed', approval: 'Review', denied: 'Denied' };
    return map[this.tool().status] ?? this.tool().status;
  });

  constructor() {
    // Auto-open the card when approval is needed so the user sees the buttons
    effect(() => {
      this.open.set(this.tool().status === 'approval');
    }, { allowSignalWrites: true });
  }

  toggleOpen(): void { this.open.update(v => !v); }
  approve(): void { void this.chatbot.respondToToolApproval(this.tool().id, true); }
  deny(): void { void this.chatbot.respondToToolApproval(this.tool().id, false); }

  formatOutput(output: unknown): string {
    if (typeof output === 'string') return output;
    return JSON.stringify(output, null, 2);
  }
}
