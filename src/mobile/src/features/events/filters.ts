import type { EventFilters } from '@/api/events';

export type ChipId = 'all' | 'trail' | 'road' | 'thisMonth' | '21' | '42' | 'north';

export const CHIPS: { id: ChipId; label: string }[] = [
  { id: 'all', label: 'Tất cả' },
  { id: 'trail', label: 'Trail' },
  { id: 'road', label: 'Đường nhựa' },
  { id: 'thisMonth', label: 'Tháng này' },
  { id: '21', label: '21K' },
  { id: '42', label: '42K' },
  { id: 'north', label: 'Miền Bắc' },
];

const pad = (n: number) => String(n).padStart(2, '0');
export const isoDate = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const endOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth() + 1, 0);

/** The filters a chip controls (the search text is separate). */
export function hasChipFilters(f: EventFilters): boolean {
  return Boolean(f.type || f.distance?.length || f.region || f.from || f.to);
}

export function isChipActive(f: EventFilters, chip: ChipId, today: Date): boolean {
  switch (chip) {
    case 'all':
      return !hasChipFilters(f);
    case 'trail':
    case 'road':
      return f.type === chip;
    case 'thisMonth':
      return f.from === isoDate(today) && f.to === isoDate(endOfMonth(today));
    case '21':
    case '42':
      return Boolean(f.distance?.includes(chip));
    case 'north':
      return f.region === 'north';
  }
}

/** Tapping a chip turns it on, or off if it is already on. "Tất cả" clears every chip. */
export function toggleChip(f: EventFilters, chip: ChipId, today: Date): EventFilters {
  if (chip === 'all') return {};
  if (isChipActive(f, chip, today)) {
    switch (chip) {
      case 'trail':
      case 'road':
        return { ...f, type: undefined };
      case 'thisMonth':
        return { ...f, from: undefined, to: undefined };
      case '21':
      case '42': {
        const rest = (f.distance ?? []).filter((d) => d !== chip);
        return { ...f, distance: rest.length ? rest : undefined };
      }
      case 'north':
        return { ...f, region: undefined };
    }
  }
  switch (chip) {
    case 'trail':
    case 'road':
      return { ...f, type: chip };
    case 'thisMonth':
      return { ...f, from: isoDate(today), to: isoDate(endOfMonth(today)) };
    case '21':
    case '42':
      return { ...f, distance: [...(f.distance ?? []), chip] };
    case 'north':
      return { ...f, region: 'north' };
  }
}
