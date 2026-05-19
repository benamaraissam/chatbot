import { Component, ChangeDetectionStrategy, signal, computed, effect, inject } from '@angular/core';
import { ChatbotService } from '../../../chatbot-angular/src/lib/services/chatbot.service';
import { FloatingChatbotComponent } from '../../../chatbot-angular/src/lib/components/floating-chatbot/floating-chatbot.component';
import { ChatWindowComponent } from '../../../chatbot-angular/src/lib/components/chat-window/chat-window.component';
import type { ThemeMode } from '../../../chatbot-angular/src/lib/utils/theme';

type DisplayMode = 'floating' | 'embedded';

const THEMES: { value: ThemeMode; label: string }[] = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
];

const PRIMARY_COLORS: { label: string; value: string | undefined; swatch?: string }[] = [
  { label: 'Default', value: undefined },
  { label: 'Violet', value: '#7c3aed', swatch: '#7c3aed' },
  { label: 'Blue', value: '#2563eb', swatch: '#2563eb' },
  { label: 'Teal', value: '#0d9488', swatch: '#0d9488' },
  { label: 'Rose', value: '#e11d48', swatch: '#e11d48' },
];

const DEMO_PROMPTS = [
  'thinking demo',
  "What's the weather in Paris?",
  'full demo',
  'send approval email',
  'skill demo',
  'markdown demo',
];

@Component({
  selector: 'app-root',
  standalone: true,
  providers: [ChatbotService],
  imports: [FloatingChatbotComponent, ChatWindowComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '[class]': '"demo-app demo-app--" + displayMode()' },
  template: `
    <!-- Demo background -->
    <div class="demo-bg" aria-hidden="true">
      <div class="demo-grid"></div>
    </div>

    <!-- Config panel -->
    <main class="demo-shell" [attr.data-cb-theme]="resolvedThemeAttr()">
      <span class="demo-badge">Angular + FastAPI</span>
      <h1 class="demo-title">Chatbot component demo</h1>
      <p class="demo-lead">
        Configure the chat below. Switch display mode to try floating or sidebar
        integration — this page stays in place.
      </p>

      <div class="demo-stack">

        <!-- Integration card -->
        <section class="demo-card">
          <h2 class="demo-card-title">Integration</h2>
          <div class="demo-field">
            <span class="demo-field-label">Display mode</span>
            <div class="demo-segment" role="group" aria-label="Chat display mode">
              <button type="button"
                [class]="'demo-segment-btn' + (displayMode() === 'floating' ? ' demo-segment-btn--active' : '')"
                (click)="displayMode.set('floating')">Floating</button>
              <button type="button"
                [class]="'demo-segment-btn' + (displayMode() === 'embedded' ? ' demo-segment-btn--active' : '')"
                (click)="displayMode.set('embedded')">Sidebar</button>
            </div>
            <p class="demo-field-hint">
              {{ displayMode() === 'floating'
                ? 'FloatingChatbot · hostLayout="overlay"'
                : 'ChatWindow embedded · hostLayout="block"' }}
            </p>
          </div>
        </section>

        <!-- Appearance card -->
        <section class="demo-card">
          <h2 class="demo-card-title">Appearance</h2>

          <div class="demo-field">
            <span class="demo-field-label">File attachments</span>
            <div class="demo-segment" role="group" aria-label="File attachments">
              <button type="button"
                [class]="'demo-segment-btn' + (attachmentsEnabled() ? ' demo-segment-btn--active' : '')"
                (click)="attachmentsEnabled.set(true)">Enabled</button>
              <button type="button"
                [class]="'demo-segment-btn' + (!attachmentsEnabled() ? ' demo-segment-btn--active' : '')"
                (click)="attachmentsEnabled.set(false)">Disabled</button>
            </div>
          </div>

          <div class="demo-field">
            <span class="demo-field-label">Theme</span>
            <div class="demo-segment" role="group" aria-label="Chat theme">
              @for (t of themes; track t.value) {
                <button type="button"
                  [class]="'demo-segment-btn' + (theme() === t.value ? ' demo-segment-btn--active' : '')"
                  (click)="theme.set(t.value)">{{ t.label }}</button>
              }
            </div>
          </div>

          <div class="demo-field">
            <span class="demo-field-label">Primary color</span>
            <div class="demo-colors">
              @for (c of primaryColors; track c.label) {
                <button type="button"
                  [class]="'demo-color-btn' + (primaryColor() === c.value ? ' demo-color-btn--active' : '')"
                  (click)="primaryColor.set(c.value)">
                  <span
                    [class]="'demo-swatch' + (!c.swatch ? ' demo-swatch--default' : '')"
                    [style]="c.swatch ? 'background:' + c.swatch : ''"
                    aria-hidden="true"></span>
                  {{ c.label }}
                </button>
              }
            </div>
          </div>
        </section>

        <!-- Sample prompts card -->
        <section class="demo-card">
          <h2 class="demo-card-title">Sample prompts</h2>
          <div class="demo-prompts">
            @for (p of prompts; track p) {
              <span class="demo-prompt">{{ p }}</span>
            }
          </div>
          <p class="demo-code">
            <strong>Backend:</strong> http://localhost:8000/api/chat/chat<br>
            <strong>Run:</strong> cd ../chatbot-python-library &amp;&amp; python examples/02_web_apps/bot.py
          </p>
        </section>

        <p class="demo-footer">
          Floating: button bottom-right ↘ · Sidebar: panel docked on the right →
        </p>
      </div>
    </main>

    <!-- Floating chatbot -->
    @if (displayMode() === 'floating') {
      <cb-floating-chatbot />
    }

    <!-- Embedded sidebar (cb-root--block inside is positioned by demo CSS) -->
    @if (displayMode() === 'embedded') {
      <cb-chat-window [embedded]="true" [collapsible]="true" />
    }
  `,
  styles: [`
    :host {
      display: block;
      position: relative;
      width: 100%;
      height: 100%;
      min-height: 0;
    }
  `],
})
export class AppComponent {
  readonly chatbot = inject(ChatbotService);

  readonly displayMode = signal<DisplayMode>('floating');
  readonly theme = signal<ThemeMode>('system');
  readonly primaryColor = signal<string | undefined>(undefined);
  readonly attachmentsEnabled = signal(true);

  readonly themes = THEMES;
  readonly primaryColors = PRIMARY_COLORS;
  readonly prompts = DEMO_PROMPTS;

  readonly resolvedThemeAttr = computed(() =>
    this.chatbot.resolvedTheme() === 'light' ? 'light' : undefined
  );

  constructor() {
    // Sync theme → chatbotService
    effect(() => {
      this.chatbot.setTheme(this.theme());
    }, { allowSignalWrites: true });
    // Sync primaryColor → chatbotService
    effect(() => {
      this.chatbot.setPrimaryColor(this.primaryColor());
    }, { allowSignalWrites: true });
    // Sync attachmentsEnabled → chatbotService
    effect(() => {
      this.chatbot.setAttachmentsEnabled(this.attachmentsEnabled());
    }, { allowSignalWrites: true });
  }
}
