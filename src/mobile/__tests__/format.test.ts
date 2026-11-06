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
