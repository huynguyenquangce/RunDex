import { fireEvent, render, screen } from '@testing-library/react-native';

import type { EventSummary } from '@/api/events';
import { EventCard } from '@/components/EventCard';

const EVENT: EventSummary = {
  slug: 'vietnam-trail-marathon-2027',
  name: 'Vietnam Trail Marathon 2027',
  organizer: null,
  event_type: 'trail',
  start_date: '2027-01-16',
  end_date: null,
  province: 'Sơn La',
  venue: 'Mộc Châu',
  status: 'registration_open',
  closing_soon: false,
  days_left: null,
  verified: true,
  last_verified_at: null,
  distances: [
    { label: '70K', distance_km: 70 },
    { label: '21K', distance_km: 21 },
  ],
};

describe('<EventCard />', () => {
  it('shows the date block, badges, name, place and distances', async () => {
    await render(<EventCard event={EVENT} onPress={() => {}} />);
    expect(screen.getByText('16')).toBeTruthy();
    expect(screen.getByText('THG 1')).toBeTruthy();
    expect(screen.getByText('Trail')).toBeTruthy();
    expect(screen.getByText('Đang mở đăng ký')).toBeTruthy();
    expect(screen.getByText('Vietnam Trail Marathon 2027')).toBeTruthy();
    expect(screen.getByText('Mộc Châu, Sơn La')).toBeTruthy();
    expect(screen.getByText('70K · 21K')).toBeTruthy();
  });

  it('has an accessible summary and reacts to a press', async () => {
    const onPress = jest.fn();
    await render(<EventCard event={EVENT} onPress={onPress} />);
    const card = screen.getByRole('button');
    expect(card.props.accessibilityLabel).toContain('16/01/2027');
    await fireEvent.press(card);
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('falls back gracefully when the place and distances are unknown', async () => {
    await render(
      <EventCard event={{ ...EVENT, venue: null, province: null, distances: [] }} onPress={() => {}} />,
    );
    expect(screen.getByText('Việt Nam')).toBeTruthy();
    expect(screen.queryByText('70K · 21K')).toBeNull();
  });
});
