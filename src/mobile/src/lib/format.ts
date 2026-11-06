/** "2027-01-16" -> "16/01/2027" (string based, no timezone surprises). */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split('-');
  return `${day}/${month}/${year}`;
}

/** Short Vietnamese label for an event's effective status. */
export function statusLabel(status: string): string {
  switch (status) {
    case 'registration_open':
      return 'Đang mở đăng ký';
    case 'registration_closed':
      return 'Đã đóng đăng ký';
    case 'scheduled':
      return 'Chưa mở đăng ký';
    case 'postponed':
      return 'Hoãn';
    case 'cancelled':
      return 'Đã hủy';
    case 'completed':
      return 'Đã diễn ra';
    default:
      return status;
  }
}

const MONTH_LABEL = 'THG';

/** "2027-01-16" -> "16" */
export function dayLabel(iso: string): string {
  return String(Number(iso.split('-')[2]));
}

/** "2027-01-16" -> "THG 1" */
export function monthLabel(iso: string): string {
  return `${MONTH_LABEL} ${Number(iso.split('-')[1])}`;
}

/** [{label: "42K"}, {label: "21K"}] -> "42K · 21K" */
export function distancesLabel(distances: { label: string }[]): string {
  return distances.map((d) => d.label).join(' · ');
}

export function typeLabel(eventType: string): string {
  switch (eventType) {
    case 'trail':
      return 'Trail';
    case 'road':
      return 'Đường nhựa';
    default:
      return 'Kết hợp';
  }
}

export type Tone = 'ok' | 'warn' | 'muted' | 'danger';

/** What the status badge on a card says and how it is coloured. */
export function statusBadge(event: {
  status: string;
  closing_soon: boolean;
  days_left?: number | null;
}): { label: string; tone: Tone } {
  if (event.closing_soon && event.days_left != null) {
    return { label: event.days_left === 0 ? 'Hôm nay là hạn cuối' : `Còn ${event.days_left} ngày`, tone: 'warn' };
  }
  switch (event.status) {
    case 'registration_open':
      return { label: 'Đang mở đăng ký', tone: 'ok' };
    case 'postponed':
      return { label: 'Hoãn', tone: 'warn' };
    case 'cancelled':
      return { label: 'Đã hủy', tone: 'danger' };
    default:
      return { label: statusLabel(event.status), tone: 'muted' };
  }
}
