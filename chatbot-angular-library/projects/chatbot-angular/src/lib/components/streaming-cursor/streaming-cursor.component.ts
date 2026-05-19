import { Component, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'cb-streaming-cursor',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<span class="cb-streaming-cursor" aria-hidden="true">▋</span>`,
  styles: [`
    .cb-streaming-cursor {
      display: inline-block;
      width: 2px;
      height: 1.1em;
      background: currentColor;
      margin-left: 1px;
      vertical-align: text-bottom;
      border-radius: 1px;
      animation: cb-cursor-blink 0.9s steps(2) infinite;
      font-size: 0;
      overflow: hidden;
    }
    @keyframes cb-cursor-blink {
      0% { opacity: 1; }
      50% { opacity: 0; }
    }
  `],
})
export class StreamingCursorComponent {}
