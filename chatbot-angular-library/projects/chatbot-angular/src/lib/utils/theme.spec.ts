import { resolveTheme } from './theme';

describe('resolveTheme', () => {
  it('returns the explicit mode for "light"', () => {
    expect(resolveTheme('light')).toBe('light');
  });

  it('returns the explicit mode for "dark"', () => {
    expect(resolveTheme('dark')).toBe('dark');
  });

  it('falls back to "light" when system preference cannot be determined', () => {
    const original = window.matchMedia;
    // Force the no-match branch by stubbing matchMedia.
    (window as unknown as { matchMedia?: (q: string) => MediaQueryList }).matchMedia =
      () => ({ matches: false } as MediaQueryList);
    try {
      expect(resolveTheme('system')).toBe('light');
    } finally {
      window.matchMedia = original;
    }
  });

  it('returns "dark" when the system reports a dark colour scheme', () => {
    const original = window.matchMedia;
    (window as unknown as { matchMedia?: (q: string) => MediaQueryList }).matchMedia =
      () => ({ matches: true } as MediaQueryList);
    try {
      expect(resolveTheme('system')).toBe('dark');
    } finally {
      window.matchMedia = original;
    }
  });
});
