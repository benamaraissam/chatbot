import { Component, ChangeDetectionStrategy, input, computed, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Component({
  selector: 'cb-markdown-message',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="cb-prose [&_p]:cb-my-2 [&_p:first-child]:cb-mt-0 [&_p:last-child]:cb-mb-0 [&_h1]:cb-text-lg [&_h1]:cb-font-semibold [&_h2]:cb-text-base [&_h2]:cb-font-semibold [&_ul]:cb-my-2 [&_ul]:cb-list-disc [&_ul]:cb-pl-5 [&_ol]:cb-my-2 [&_ol]:cb-list-decimal [&_ol]:cb-pl-5 [&_blockquote]:cb-border-l-2 [&_blockquote]:cb-border-cb-border [&_blockquote]:cb-pl-3 [&_blockquote]:cb-text-cb-muted [&_a]:cb-text-cb-primary [&_a]:cb-underline [&_a]:cb-underline-offset-2 [&_table]:cb-my-2 [&_table]:cb-block [&_table]:cb-max-w-full [&_table]:cb-border-collapse [&_table]:cb-overflow-x-auto [&_table]:cb-text-xs [&_th]:cb-border [&_th]:cb-border-cb-border [&_th]:cb-px-2 [&_th]:cb-py-1 [&_th]:cb-text-left [&_th]:cb-bg-[var(--cb-surface-hover)] [&_td]:cb-border [&_td]:cb-border-cb-border [&_td]:cb-px-2 [&_td]:cb-py-1"
      [innerHTML]="renderedHtml()"
    ></div>
  `,
})
export class MarkdownMessageComponent {
  private readonly sanitizer = inject(DomSanitizer);
  readonly content = input('');

  readonly renderedHtml = computed((): SafeHtml => {
    return this.sanitizer.bypassSecurityTrustHtml(markdownToHtml(this.content()));
  });
}

/** Minimal markdown-to-HTML converter. Handles the most common cases. */
function markdownToHtml(md: string): string {
  // Code blocks (must be before inline code)
  let html = md.replace(/```(\w*)\n?([\s\S]*?)```/g, (_m, lang, code) => {
    const escaped = escapeHtml(code.trim());
    const langAttr = lang ? ` data-lang="${lang}"` : '';
    return `<div class="cb-code-block"${langAttr}><div class="cb-code-block-scroll"><pre class="cb-code-block-fallback"><code>${escaped}</code></pre></div></div>`;
  });
  // Inline code
  html = html.replace(/`([^`]+)`/g, (_, code) => `<code class="cb-inline-block cb-rounded-sm cb-bg-[var(--cb-surface-hover)] cb-px-0.5 cb-py-0.5 cb-text-[0.85em] cb-font-mono">${escapeHtml(code)}</code>`);
  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  // Unordered lists
  html = html.replace(/^[*\-] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr>');
  // Paragraphs: split by double newlines, wrap non-block-level elements
  const blocks = html.split(/\n{2,}/);
  html = blocks.map(block => {
    const trimmed = block.trim();
    if (!trimmed) return '';
    if (/^<(h[1-6]|ul|ol|blockquote|div|hr|pre|table)/.test(trimmed)) return trimmed;
    return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
  }).filter(Boolean).join('\n');
  return html;
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
