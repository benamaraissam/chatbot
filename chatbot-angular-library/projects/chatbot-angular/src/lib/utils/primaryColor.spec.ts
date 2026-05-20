import { parseColor } from './primaryColor';

describe('parseColor', () => {
  it('parses a 6-digit hex code', () => {
    expect(parseColor('#0D9488')).toEqual({ r: 13, g: 148, b: 136 });
  });

  it('parses a 3-digit shorthand hex code', () => {
    expect(parseColor('#0a4')).toEqual({ r: 0, g: 170, b: 68 });
  });

  it('parses an rgb() value', () => {
    expect(parseColor('rgb(13, 148, 136)')).toEqual({ r: 13, g: 148, b: 136 });
  });

  it('parses an rgba() value (ignores alpha component)', () => {
    expect(parseColor('rgba(13, 148, 136, 0.5)')).toEqual({ r: 13, g: 148, b: 136 });
  });

  it('returns null for empty input', () => {
    expect(parseColor('')).toBeNull();
    expect(parseColor('   ')).toBeNull();
  });

  it('returns null for malformed input', () => {
    expect(parseColor('not-a-color')).toBeNull();
    expect(parseColor('#zzz')).toBeNull();
  });
});
