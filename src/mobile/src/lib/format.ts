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
