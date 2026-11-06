import {
  CHIPS,
  activeFilterCount,
  activeTime,
  hasChipFilters,
  isChipActive,
  isoDate,
  setOpenOnly,
  setRegion,
  setTime,
  timeRange,
  toggleChip,
  toggleDistance,
} from '@/features/events/filters';

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

  it('"Tất cả" clears every filter, including "only open"', () => {
    let f = toggleChip({}, 'trail', TODAY);
    f = toggleChip(f, 'north', TODAY);
    f = toggleChip(f, '42', TODAY);
    f = setOpenOnly(f, true);
    expect(hasChipFilters(f)).toBe(true);
    expect(toggleChip(f, 'all', TODAY)).toEqual({});
  });

  it('formats dates without timezone surprises', () => {
    expect(isoDate(new Date(2027, 0, 5))).toBe('2027-01-05');
  });
});

describe('filter sheet groups', () => {
  it('knows the time ranges and recognises them again', () => {
    expect(timeRange('next3', TODAY)).toEqual({ from: '2026-11-06', to: '2027-02-06' });
    expect(timeRange('next6', TODAY)).toEqual({ from: '2026-11-06', to: '2027-05-06' });
    const f = setTime({}, 'next3', TODAY);
    expect(activeTime(f, TODAY)).toBe('next3');
    expect(activeTime({ from: '2026-01-01', to: '2026-02-01' }, TODAY)).toBeUndefined();
    expect(setTime(f, undefined, TODAY)).toEqual({ from: undefined, to: undefined });
  });

  it('keeps the other filters when one group changes', () => {
    let f = toggleDistance({ type: 'trail' }, 'ultra');
    f = setRegion(f, 'highlands');
    f = setOpenOnly(f, true);
    expect(f).toEqual({ type: 'trail', distance: ['ultra'], region: 'highlands', openOnly: true });
    expect(setOpenOnly(f, false).openOnly).toBeUndefined();
  });

  it('counts the groups in use for the filter button badge', () => {
    expect(activeFilterCount({})).toBe(0);
    expect(activeFilterCount({ type: 'trail', distance: ['21', '42'] })).toBe(2);
    const all = setOpenOnly(setTime(setRegion(toggleDistance({ type: 'road' }, '5'), 'south'), 'thisMonth', TODAY), true);
    expect(activeFilterCount(all)).toBe(5);
    expect(activeFilterCount({ distance: [] })).toBe(0);
  });
});
