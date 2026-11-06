import { formatDate, statusLabel } from '@/lib/format';

describe('formatDate', () => {
  it('formats ISO dates as dd/MM/yyyy', () => {
    expect(formatDate('2027-01-16')).toBe('16/01/2027');
  });
});

describe('statusLabel', () => {
  it('has a Vietnamese label for every API status', () => {
    for (const status of [
      'scheduled',
      'registration_open',
      'registration_closed',
      'postponed',
      'cancelled',
      'completed',
    ]) {
      expect(statusLabel(status)).not.toBe(status);
    }
  });
});

import { dayLabel, distancesLabel, monthLabel, statusBadge, typeLabel } from '@/lib/format';

describe('card helpers', () => {
  it('splits an ISO date into the day and month shown on the date block', () => {
    expect(dayLabel('2027-01-06')).toBe('6');
    expect(monthLabel('2027-01-06')).toBe('THG 1');
    expect(monthLabel('2027-12-25')).toBe('THG 12');
  });

  it('joins distance labels', () => {
    expect(distancesLabel([{ label: '42K' }, { label: '21K' }])).toBe('42K · 21K');
    expect(distancesLabel([])).toBe('');
  });

  it('names event types in Vietnamese', () => {
    expect(typeLabel('trail')).toBe('Trail');
    expect(typeLabel('road')).toBe('Đường nhựa');
    expect(typeLabel('mixed')).toBe('Kết hợp');
  });

  it('picks the status badge', () => {
    expect(statusBadge({ status: 'registration_open', closing_soon: false })).toEqual({
      label: 'Đang mở đăng ký',
      tone: 'ok',
    });
    expect(statusBadge({ status: 'registration_open', closing_soon: true, days_left: 5 })).toEqual({
      label: 'Còn 5 ngày',
      tone: 'warn',
    });
    expect(statusBadge({ status: 'cancelled', closing_soon: false }).tone).toBe('danger');
    expect(statusBadge({ status: 'scheduled', closing_soon: false }).tone).toBe('muted');
  });
});
