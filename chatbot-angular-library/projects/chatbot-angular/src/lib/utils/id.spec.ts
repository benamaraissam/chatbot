import { createId } from './id';

describe('createId', () => {
  it('uses the default prefix when none is provided', () => {
    expect(createId()).toMatch(/^id_[a-z0-9]+$/);
  });

  it('honours a custom prefix', () => {
    expect(createId('conv')).toMatch(/^conv_[a-z0-9]+$/);
  });

  it('produces unique values across many calls', () => {
    const seen = new Set<string>();
    for (let i = 0; i < 1000; i++) seen.add(createId('x'));
    // base36 of a 9-char slice — collisions across 1k calls would indicate a bug.
    expect(seen.size).toBe(1000);
  });
});
