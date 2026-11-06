import {
  deadlineLines,
  distanceDetails,
  eventDateLine,
  formatCutoff,
  formatThousands,
  formatTime,
  formatVnd,
  isHttpUrl,
  mapSearchUrl,
  weekdayLabel,
} from '@/lib/format';

describe('detail formatting', () => {
  it('names the weekday from the date itself', () => {
    expect(weekdayLabel('2027-01-16')).toBe('Thứ Bảy');
    expect(weekdayLabel('2027-01-17')).toBe('Chủ Nhật');
    expect(weekdayLabel('2026-11-06')).toBe('Thứ Sáu');
  });

  it('formats money, time and cut-off', () => {
    expect(formatThousands(3000)).toBe('3.000');
    expect(formatVnd(1000000)).toBe('1.000.000 ₫');
    expect(formatTime('05:00:00')).toBe('05:00');
    expect(formatCutoff(1200)).toBe('20 giờ');
    expect(formatCutoff(390)).toBe('6 giờ 30');
    expect(formatCutoff(45)).toBe('45 phút');
  });

  it('builds the date line for single and multi-day events', () => {
    expect(eventDateLine('2027-01-16', null, '05:00:00')).toBe('Thứ Bảy, 16/01/2027 · 05:00');
    expect(eventDateLine('2027-01-16', null)).toBe('Thứ Bảy, 16/01/2027');
    expect(eventDateLine('2027-01-15', '2027-01-17')).toBe('Thứ Sáu, 15/01 – 17/01/2027');
  });

  it('accepts only http(s) links', () => {
    expect(isHttpUrl('https://vietnamtrailseries.com/')).toBe(true);
    expect(isHttpUrl('http://example.org')).toBe(true);
    expect(isHttpUrl('javascript:alert(1)')).toBe(false);
    expect(isHttpUrl('tel:123')).toBe(false);
    expect(isHttpUrl(null)).toBe(false);
  });

  it('builds a map search link from the place', () => {
    expect(mapSearchUrl('Mộc Châu', 'Sơn La')).toBe(
      'https://www.google.com/maps/search/?api=1&query=M%E1%BB%99c%20Ch%C3%A2u%2C%20S%C6%A1n%20La',
    );
    expect(mapSearchUrl(null, null)).toBeNull();
  });

  it('writes the distance card lines and skips what is unknown', () => {
    expect(
      distanceDetails({ start_time: '05:00:00', fee_vnd: 1000000, elevation_gain_m: 3000, cutoff_minutes: 1200 }),
    ).toEqual({ primary: 'Xuất phát 05:00 · Phí 1.000.000 ₫', secondary: 'D+ 3.000 m · Cut-off 20 giờ' });
    expect(distanceDetails({})).toEqual({ primary: '', secondary: '' });
  });

  it('explains the registration deadline', () => {
    expect(deadlineLines('2026-12-31', 55, 'registration_open')).toEqual({
      title: 'Hạn đăng ký: 31/12/2026',
      sub: 'Còn 55 ngày',
    });
    expect(deadlineLines('2026-11-06', 0, 'registration_open')?.sub).toBe('Hôm nay là hạn cuối');
    expect(deadlineLines('2026-10-01', null, 'registration_open')?.sub).toBe('Đã hết hạn');
    expect(deadlineLines('2026-10-01', null, 'registration_closed')?.sub).toBe('Đã đóng đăng ký');
    expect(deadlineLines(null, null, 'scheduled')).toBeNull();
  });
});
