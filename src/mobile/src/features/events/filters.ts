import type { DistanceBucket, EventFilters, Region } from '@/api/events';

// ---- helpers --------------------------------------------------------------------------------

const pad = (n: number) => String(n).padStart(2, '0');
export const isoDate = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const endOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth() + 1, 0);
const addMonths = (d: Date, n: number) => new Date(d.getFullYear(), d.getMonth() + n, d.getDate());

// ---- time ranges ------------------------------------------------------------------------------

export type TimeId = 'thisMonth' | 'next3' | 'next6';

export const TIME_OPTIONS: { id: TimeId; label: string }[] = [
  { id: 'thisMonth', label: 'Tháng này' },
  { id: 'next3', label: '3 tháng tới' },
  { id: 'next6', label: '6 tháng tới' },
];

export function timeRange(id: TimeId, today: Date): { from: string; to: string } {
  const from = isoDate(today);
  switch (id) {
    case 'thisMonth':
      return { from, to: isoDate(endOfMonth(today)) };
    case 'next3':
      return { from, to: isoDate(addMonths(today, 3)) };
    case 'next6':
      return { from, to: isoDate(addMonths(today, 6)) };
  }
}

export function activeTime(f: EventFilters, today: Date): TimeId | undefined {
  return TIME_OPTIONS.find((o) => {
    const r = timeRange(o.id, today);
    return f.from === r.from && f.to === r.to;
  })?.id;
}

// ---- filter groups (shared by the quick chips and the filter sheet) ---------------------------

export const TYPE_OPTIONS = [
  { id: 'trail', label: 'Trail' },
  { id: 'road', label: 'Đường nhựa' },
] as const;

export const DISTANCE_OPTIONS: { id: DistanceBucket; label: string }[] = [
  { id: '5', label: '5K' },
  { id: '10', label: '10K' },
  { id: '21', label: '21K' },
  { id: '42', label: '42K' },
  { id: 'ultra', label: '50K+' },
];

export const REGION_OPTIONS: { id: Region; label: string }[] = [
  { id: 'north', label: 'Miền Bắc' },
  { id: 'central', label: 'Miền Trung' },
  { id: 'highlands', label: 'Tây Nguyên' },
  { id: 'south', label: 'Miền Nam' },
];

export const setType = (f: EventFilters, type: 'trail' | 'road' | undefined): EventFilters => ({ ...f, type });

export const toggleDistance = (f: EventFilters, id: DistanceBucket): EventFilters => {
  const current = f.distance ?? [];
  const next = current.includes(id) ? current.filter((d) => d !== id) : [...current, id];
  return { ...f, distance: next.length ? next : undefined };
};

export const setRegion = (f: EventFilters, region: Region | undefined): EventFilters => ({ ...f, region });

export const setTime = (f: EventFilters, id: TimeId | undefined, today: Date): EventFilters =>
  id ? { ...f, ...timeRange(id, today) } : { ...f, from: undefined, to: undefined };

export const setOpenOnly = (f: EventFilters, openOnly: boolean): EventFilters => ({
  ...f,
  openOnly: openOnly || undefined,
});

/** The filters the chips and the sheet control (the search text is separate). */
export function hasChipFilters(f: EventFilters): boolean {
  return Boolean(f.type || f.distance?.length || f.region || f.from || f.to || f.openOnly);
}

/** Number of filter groups in use: shown as a badge on the filter button. */
export function activeFilterCount(f: EventFilters): number {
  return [f.type, f.distance?.length, f.region, f.from || f.to, f.openOnly].filter(Boolean).length;
}

// ---- quick chips on the list screen -------------------------------------------------------------

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

export function isChipActive(f: EventFilters, chip: ChipId, today: Date): boolean {
  switch (chip) {
    case 'all':
      return !hasChipFilters(f);
    case 'trail':
    case 'road':
      return f.type === chip;
    case 'thisMonth':
      return activeTime(f, today) === 'thisMonth';
    case '21':
    case '42':
      return Boolean(f.distance?.includes(chip));
    case 'north':
      return f.region === 'north';
  }
}

/** Tapping a chip turns it on, or off if it is already on. "Tất cả" clears every filter. */
export function toggleChip(f: EventFilters, chip: ChipId, today: Date): EventFilters {
  const on = isChipActive(f, chip, today);
  switch (chip) {
    case 'all':
      return {};
    case 'trail':
    case 'road':
      return setType(f, on ? undefined : chip);
    case 'thisMonth':
      return setTime(f, on ? undefined : 'thisMonth', today);
    case '21':
    case '42':
      return toggleDistance(f, chip);
    case 'north':
      return setRegion(f, on ? undefined : 'north');
  }
}
