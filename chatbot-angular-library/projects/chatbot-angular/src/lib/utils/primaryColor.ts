import type { ResolvedTheme } from './theme';

interface Rgb { r: number; g: number; b: number }

function clamp01(n: number): number { return Math.min(1, Math.max(0, n)); }
function clamp255(n: number): number { return Math.min(255, Math.max(0, Math.round(n))); }

function mix(a: Rgb, b: Rgb, amount: number): Rgb {
  const t = clamp01(amount);
  return { r: clamp255(a.r + (b.r - a.r) * t), g: clamp255(a.g + (b.g - a.g) * t), b: clamp255(a.b + (b.b - a.b) * t) };
}

function relativeLuminance({ r, g, b }: Rgb): number {
  const toLinear = (c: number) => { const s = c / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

export function parseColor(input: string): Rgb | null {
  const s = input.trim();
  if (!s) return null;
  if (s.startsWith('#')) {
    let hex = s.slice(1);
    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
    if (hex.length !== 6 && hex.length !== 8) return null;
    const n = Number.parseInt(hex.slice(0, 6), 16);
    if (Number.isNaN(n)) return null;
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
  }
  const m = s.match(/^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i);
  if (m) return { r: clamp255(Number(m[1])), g: clamp255(Number(m[2])), b: clamp255(Number(m[3])) };
  return null;
}

function rgbToHex({ r, g, b }: Rgb): string {
  return `#${[r, g, b].map(c => c.toString(16).padStart(2, '0')).join('')}`;
}

function rgba({ r, g, b }: Rgb, alpha: number): string {
  return `rgba(${r}, ${g}, ${b}, ${clamp01(alpha)})`;
}

/** Returns a Record of CSS custom properties for the given brand color. */
export function buildPrimaryColorStyle(
  color: string,
  resolvedTheme: ResolvedTheme,
): Record<string, string> | undefined {
  const rgb = parseColor(color);
  if (!rgb) return undefined;

  const primary = rgbToHex(rgb);
  const hover = resolvedTheme === 'dark'
    ? rgbToHex(mix(rgb, { r: 255, g: 255, b: 255 }, 0.18))
    : rgbToHex(mix(rgb, { r: 0, g: 0, b: 0 }, 0.12));
  const fg = relativeLuminance(rgb) > 0.55 ? '#111827' : '#ffffff';
  const mutedAlpha = resolvedTheme === 'dark' ? 0.15 : 0.1;
  const glowAlpha = resolvedTheme === 'dark' ? 0.4 : 0.25;
  const thinkingBgAlpha = resolvedTheme === 'dark' ? 0.08 : 0.06;
  const thinkingBorderAlpha = resolvedTheme === 'dark' ? 0.22 : 0.18;
  const userBubble = resolvedTheme === 'dark'
    ? rgbToHex(mix(rgb, { r: 0, g: 0, b: 0 }, 0.32)) : primary;
  const userBubbleHover = resolvedTheme === 'dark'
    ? rgbToHex(mix(rgb, { r: 0, g: 0, b: 0 }, 0.22)) : hover;
  const thinkingLabel = resolvedTheme === 'dark'
    ? rgbToHex(mix(rgb, { r: 255, g: 255, b: 255 }, 0.28)) : primary;
  const thinkingText = resolvedTheme === 'dark'
    ? rgbToHex(mix(rgb, { r: 255, g: 255, b: 255 }, 0.52))
    : rgbToHex(mix(rgb, { r: 0, g: 0, b: 0 }, 0.35));

  return {
    '--cb-primary': primary,
    '--cb-primary-hover': hover,
    '--cb-primary-fg': fg,
    '--cb-primary-muted': rgba(rgb, mutedAlpha),
    '--cb-primary-glow': rgba(rgb, glowAlpha),
    '--cb-user-bubble': userBubble,
    '--cb-user-bubble-hover': userBubbleHover,
    '--cb-user-text': fg,
    '--cb-thinking-bg': rgba(rgb, thinkingBgAlpha),
    '--cb-thinking-border': rgba(rgb, thinkingBorderAlpha),
    '--cb-thinking-label': thinkingLabel,
    '--cb-thinking-text': thinkingText,
  };
}
