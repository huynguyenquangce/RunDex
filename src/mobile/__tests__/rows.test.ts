import type { EventSummary } from '@/api/events';
import { monthHeading, withMonthHeaders } from '@/features/events/rows';

const ev = (slug: string, start_date: string) => ({ slug, start_date }) as EventSummary;

describe('withMonthHeaders', () => {
  it('puts one header before the first event of each month', () => {
    const rows = withMonthHeaders([
      ev('a', '2026-12-30'),
      ev('b', '2026-12-31'),
      ev('c', '2027-01-02'),
    ]);
    expect(rows.map((r) => (r.kind === 'month' ? r.label : r.key))).toEqual([
      'Tháng 12 · 2026',
      'a',
      'b',
      'Tháng 1 · 2027',
      'c',
    ]);
  });

  it('separates the same month of different years and handles no events', () => {
    const rows = withMonthHeaders([ev('a', '2026-12-01'), ev('b', '2027-12-01')]);
    expect(rows.filter((r) => r.kind === 'month')).toHaveLength(2);
    expect(withMonthHeaders([])).toEqual([]);
  });

  it('formats the heading without a leading zero', () => {
    expect(monthHeading('2027-03-09')).toBe('Tháng 3 · 2027');
  });
});
