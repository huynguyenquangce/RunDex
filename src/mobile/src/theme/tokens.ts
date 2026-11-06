// Design tokens mirrored from the Figma file "RunDex - Mobile App Design" (variables "RunDex Colors").
export const colors = {
  primary: '#FF5A1F',
  primarySoft: '#FFEDE5',
  onPrimary: '#FFFFFF',
  ink: '#111827',
  muted: '#6B7280',
  surface: '#FFFFFF',
  bg: '#F5F6F8',
  border: '#E5E7EB',
  trail: '#0E7C4A',
  trailSoft: '#E4F4EB',
  road: '#1D4ED8',
  roadSoft: '#E6EDFD',
  warn: '#B45309',
  warnSoft: '#FEF3C7',
  danger: '#B91C1C',
  dangerSoft: '#FEE2E2',
  ok: '#15803D',
} as const;

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;

export const radius = { sm: 8, md: 12, lg: 16, pill: 999 } as const;

export const fontSize = { caption: 12, small: 13, body: 15, title: 20, large: 28, hero: 34 } as const;
