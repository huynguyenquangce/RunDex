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

const WEEKDAYS = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];

/** "2027-01-16" -> "Thứ Bảy" (built from local date parts, so no timezone shift). */
export function weekdayLabel(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return WEEKDAYS[new Date(y, m - 1, d).getDay()];
}

/** "05:00:00" -> "05:00" */
export function formatTime(time: string): string {
  return time.slice(0, 5);
}

/** 1000000 -> "1.000.000" */
export function formatThousands(n: number): string {
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

/** 1000000 -> "1.000.000 ₫" */
export function formatVnd(n: number): string {
  return `${formatThousands(n)} ₫`;
}

/** 1200 -> "20 giờ"; 390 -> "6 giờ 30" */
export function formatCutoff(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m} phút`;
  return m === 0 ? `${h} giờ` : `${h} giờ ${m}`;
}

/** "Thứ Bảy, 16/01/2027 · 05:00", or a range for multi-day events. */
export function eventDateLine(startDate: string, endDate: string | null | undefined, startTime?: string | null): string {
  const weekday = weekdayLabel(startDate);
  if (endDate && endDate !== startDate) {
    const short = formatDate(startDate).slice(0, 5);
    return `${weekday}, ${short} – ${formatDate(endDate)}`;
  }
  const base = `${weekday}, ${formatDate(startDate)}`;
  return startTime ? `${base} · ${formatTime(startTime)}` : base;
}

export function isHttpUrl(url: string | null | undefined): url is string {
  return typeof url === 'string' && /^https?:\/\//i.test(url);
}

/** A map search link for the event's place when the data has no explicit map URL. */
export function mapSearchUrl(venue?: string | null, province?: string | null): string | null {
  const place = [venue, province].filter(Boolean).join(', ');
  return place ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place)}` : null;
}

/** The two detail lines shown on a distance card. */
export function distanceDetails(d: {
  start_time?: string | null;
  fee_vnd?: number | null;
  elevation_gain_m?: number | null;
  cutoff_minutes?: number | null;
}): { primary: string; secondary: string } {
  const primary = [
    d.start_time ? `Xuất phát ${formatTime(d.start_time)}` : null,
    d.fee_vnd != null ? `Phí ${formatVnd(d.fee_vnd)}` : null,
  ].filter(Boolean);
  const secondary = [
    d.elevation_gain_m != null ? `D+ ${formatThousands(d.elevation_gain_m)} m` : null,
    d.cutoff_minutes != null ? `Cut-off ${formatCutoff(d.cutoff_minutes)}` : null,
  ].filter(Boolean);
  return { primary: primary.join(' · '), secondary: secondary.join(' · ') };
}

/** How the registration deadline reads on the detail screen. */
export function deadlineLines(
  deadline: string | null | undefined,
  daysLeft: number | null | undefined,
  status: string,
): { title: string; sub: string } | null {
  if (!deadline) return null;
  const title = `Hạn đăng ký: ${formatDate(deadline)}`;
  if (status === 'registration_closed') return { title, sub: 'Đã đóng đăng ký' };
  if (daysLeft == null) return { title, sub: 'Đã hết hạn' };
  return { title, sub: daysLeft === 0 ? 'Hôm nay là hạn cuối' : `Còn ${daysLeft} ngày` };
}
