import type { EventSummary } from '@/api/events';

export type ListRow =
  | { kind: 'month'; key: string; label: string }
  | { kind: 'event'; key: string; event: EventSummary };

/** "2027-01-16" -> "Tháng 1 · 2027" */
export function monthHeading(iso: string): string {
  const [year, month] = iso.split('-');
  return `Tháng ${Number(month)} · ${year}`;
}

/**
 * Events are sorted by date, so a month header goes in front of the first event of each month.
 * Counts are not shown: the list is paged, so a per-month count would be wrong until the end.
 */
export function withMonthHeaders(events: EventSummary[]): ListRow[] {
  const rows: ListRow[] = [];
  let current = '';
  for (const event of events) {
    const month = event.start_date.slice(0, 7);
    if (month !== current) {
      current = month;
      rows.push({ kind: 'month', key: `month-${month}`, label: monthHeading(event.start_date) });
    }
    rows.push({ kind: 'event', key: event.slug, event });
  }
  return rows;
}
