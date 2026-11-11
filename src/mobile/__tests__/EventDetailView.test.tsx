import { fireEvent, render, screen } from '@testing-library/react-native';

import type { EventDetail } from '@/api/events';
import { EventDetailView } from '@/components/EventDetailView';

const EVENT: EventDetail = {
  slug: 'vietnam-trail-marathon-2027',
  name: 'Vietnam Trail Marathon 2027',
  organizer: 'Topas Travel',
  event_type: 'trail',
  start_date: '2027-01-16',
  end_date: null,
  province: 'Sơn La',
  venue: 'Mộc Châu',
  status: 'registration_open',
  closing_soon: false,
  days_left: 55,
  verified: true,
  last_verified_at: '2026-11-06T09:00:00Z',
  description: null,
  map_url: null,
  registration_url: 'https://vietnamtrailseries.com/trail-marathon/vtm-book-now/',
  registration_deadline: '2026-12-31',
  source_name: 'Vietnam Trail Series',
  source_url: 'https://vietnamtrailseries.com/trail-marathon/',
  distances: [
    {
      label: '70K',
      distance_km: 70,
      start_time: '05:00:00',
      fee_vnd: 1000000,
      elevation_gain_m: 3000,
      cutoff_minutes: 1200,
      registration_deadline: null,
    },
    { label: '21K', distance_km: 21 },
  ],
};

describe('<EventDetailView />', () => {
  it('shows the event facts, deadline, distances and the source', async () => {
    await render(<EventDetailView event={EVENT} onOpenUrl={() => {}} />);
    expect(screen.getByText('Vietnam Trail Marathon 2027')).toBeTruthy();
    expect(screen.getByText('Thứ Bảy, 16/01/2027 · 05:00')).toBeTruthy();
    expect(screen.getByText('Mộc Châu, Sơn La')).toBeTruthy();
    expect(screen.getByText('Ban tổ chức: Topas Travel')).toBeTruthy();
    expect(screen.getByText('Hạn đăng ký: 31/12/2026')).toBeTruthy();
    expect(screen.getByText('Còn 55 ngày')).toBeTruthy();
    expect(screen.getByText('70K')).toBeTruthy();
    expect(screen.getByText('Xuất phát 05:00 · Phí 1.000.000 ₫')).toBeTruthy();
    expect(screen.getByText('D+ 3.000 m · Cut-off 20 giờ')).toBeTruthy();
    expect(screen.getByText('Chưa có thông tin chi tiết')).toBeTruthy();
    expect(screen.getByText(/Kiểm tra lần cuối 06\/11\/2026/)).toBeTruthy();
  });

  it('opens the organizer page from the main button and the map from the place', async () => {
    const onOpenUrl = jest.fn();
    await render(<EventDetailView event={EVENT} onOpenUrl={onOpenUrl} />);
    await fireEvent.press(screen.getByLabelText('Đăng ký trên trang ban tổ chức'));
    expect(onOpenUrl).toHaveBeenLastCalledWith('https://vietnamtrailseries.com/trail-marathon/vtm-book-now/');
    await fireEvent.press(screen.getByText('Xem bản đồ'));
    expect(onOpenUrl.mock.calls.at(-1)?.[0]).toContain('google.com/maps/search');
  });

  it('hides the registration button and explains a cancelled event', async () => {
    await render(<EventDetailView event={{ ...EVENT, status: 'cancelled' }} onOpenUrl={() => {}} />);
    expect(screen.getByText('Giải đã bị hủy.')).toBeTruthy();
    expect(screen.queryByLabelText('Đăng ký trên trang ban tổ chức')).toBeNull();
    expect(screen.queryByLabelText('Xem trang ban tổ chức')).toBeNull();
  });

  it('offers a secondary button while registration is not open', async () => {
    await render(<EventDetailView event={{ ...EVENT, status: 'scheduled' }} onOpenUrl={() => {}} />);
    expect(screen.queryByLabelText('Đăng ký trên trang ban tổ chức')).toBeNull();
    expect(screen.getByLabelText('Xem trang ban tổ chức')).toBeTruthy();
  });

  it('falls back to the source page when there is no registration link', async () => {
    const onOpenUrl = jest.fn();
    await render(<EventDetailView event={{ ...EVENT, registration_url: null }} onOpenUrl={onOpenUrl} />);
    expect(screen.getByText('Mở trang nguồn trong trình duyệt')).toBeTruthy();
    await fireEvent.press(screen.getByText('Xem trang nguồn'));
    expect(onOpenUrl).toHaveBeenCalledWith('https://vietnamtrailseries.com/trail-marathon/');
  });

  it('shows no button at all when no link exists, and says the event is not verified', async () => {
    const event = { ...EVENT, registration_url: null, source_url: null, last_verified_at: null };
    await render(<EventDetailView event={event} onOpenUrl={() => {}} />);
    expect(screen.queryByText('Mở trang của ban tổ chức trong trình duyệt')).toBeNull();
    expect(screen.getByText(/Chưa được kiểm chứng/)).toBeTruthy();
  });

  it('ignores links that are not http(s)', async () => {
    const event = { ...EVENT, registration_url: 'javascript:alert(1)', source_url: null };
    await render(<EventDetailView event={event} onOpenUrl={() => {}} />);
    expect(screen.queryByLabelText('Đăng ký trên trang ban tổ chức')).toBeNull();
  });
});

describe('about-data link', () => {
  it('opens the data explanation when the screen provides it', async () => {
    const onOpenAbout = jest.fn();
    await render(<EventDetailView event={EVENT} onOpenUrl={jest.fn()} onOpenAbout={onOpenAbout} />);
    fireEvent.press(screen.getByRole('link', { name: /Về dữ liệu/ }));
    expect(onOpenAbout).toHaveBeenCalledTimes(1);
  });

  it('shows no link without the handler', async () => {
    await render(<EventDetailView event={EVENT} onOpenUrl={jest.fn()} />);
    expect(screen.queryByText(/Về dữ liệu/)).toBeNull();
  });
});
