import { CHIPS, hasChipFilters, isChipActive, isoDate, toggleChip } from '@/features/events/filters';

const TODAY = new Date(2026, 10, 6); // 6 Nov 2026

describe('chip filters', () => {
  it('starts with "Tất cả" active and nothing else', () => {
    expect(isChipActive({}, 'all', TODAY)).toBe(true);
    for (const chip of CHIPS.filter((c) => c.id !== 'all')) {
      expect(isChipActive({}, chip.id, TODAY)).toBe(false);
    }
  });

  it('turns a type chip on and off, and the two types exclude each other', () => {
    const trail = toggleChip({}, 'trail', TODAY);
    expect(trail.type).toBe('trail');
    expect(isChipActive(trail, 'all', TODAY)).toBe(false);
    expect(toggleChip(trail, 'road', TODAY).type).toBe('road');
    expect(toggleChip(trail, 'trail', TODAY).type).toBeUndefined();
  });

  it('"Tháng này" sets today..end of month', () => {
    const f = toggleChip({}, 'thisMonth', TODAY);
    expect(f.from).toBe('2026-11-06');
    expect(f.to).toBe('2026-11-30');
    expect(isChipActive(f, 'thisMonth', TODAY)).toBe(true);
    expect(toggleChip(f, 'thisMonth', TODAY)).toEqual({ from: undefined, to: undefined });
  });

  it('distance chips combine and can be removed one by one', () => {
    let f = toggleChip({}, '21', TODAY);
    f = toggleChip(f, '42', TODAY);
    expect(f.distance).toEqual(['21', '42']);
    f = toggleChip(f, '21', TODAY);
    expect(f.distance).toEqual(['42']);
    f = toggleChip(f, '42', TODAY);
    expect(f.distance).toBeUndefined();
    expect(hasChipFilters(f)).toBe(false);
  });

  it('"Tất cả" clears every chip filter', () => {
    let f = toggleChip({}, 'trail', TODAY);
    f = toggleChip(f, 'north', TODAY);
    f = toggleChip(f, '42', TODAY);
    expect(hasChipFilters(f)).toBe(true);
    expect(toggleChip(f, 'all', TODAY)).toEqual({});
  });

  it('formats dates without timezone surprises', () => {
    expect(isoDate(new Date(2027, 0, 5))).toBe('2027-01-05');
  });
});
