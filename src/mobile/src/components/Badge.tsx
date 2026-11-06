import { StyleSheet, Text, View } from 'react-native';

import type { Tone } from '@/lib/format';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

const TONES = {
  ok: { fg: colors.ok, bg: colors.trailSoft },
  warn: { fg: colors.warn, bg: colors.warnSoft },
  muted: { fg: colors.muted, bg: colors.bg },
  danger: { fg: colors.danger, bg: colors.dangerSoft },
  trail: { fg: colors.trail, bg: colors.trailSoft },
  road: { fg: colors.road, bg: colors.roadSoft },
} as const;

export type BadgeTone = Tone | 'trail' | 'road';

export function Badge({ label, tone }: { label: string; tone: BadgeTone }) {
  const { fg, bg } = TONES[tone];
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.text, { color: fg }]} numberOfLines={1}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { borderRadius: radius.pill, paddingHorizontal: spacing.sm, paddingVertical: 3, flexShrink: 1 },
  text: { fontSize: fontSize.caption - 1, fontWeight: '500' },
});
