import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { EventSummary } from '@/api/events';
import { Badge } from '@/components/Badge';
import { Icon } from '@/components/Icon';
import { dayLabel, distancesLabel, formatDate, monthLabel, statusBadge, typeLabel } from '@/lib/format';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface Props {
  event: EventSummary;
  onPress: () => void;
}

export function EventCard({ event, onPress }: Props) {
  const status = statusBadge(event);
  const place = [event.venue, event.province].filter(Boolean).join(', ') || 'Việt Nam';
  const distances = distancesLabel(event.distances);
  const typeTone = event.event_type === 'trail' ? 'trail' : event.event_type === 'road' ? 'road' : 'muted';

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${event.name}, ${formatDate(event.start_date)}, ${place}, ${status.label}`}
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={styles.date}>
        <Text style={styles.day}>{dayLabel(event.start_date)}</Text>
        <Text style={styles.month}>{monthLabel(event.start_date)}</Text>
      </View>
      <View style={styles.info}>
        <View style={styles.badges}>
          <Badge label={typeLabel(event.event_type)} tone={typeTone} />
          <Badge label={status.label} tone={status.tone} />
        </View>
        <Text style={styles.name} numberOfLines={2}>
          {event.name}
        </Text>
        <View style={styles.place}>
          <Icon name="pin" size={14} />
          <Text style={styles.meta} numberOfLines={1}>
            {place}
          </Text>
        </View>
        {distances ? (
          <Text style={styles.meta} numberOfLines={1}>
            {distances}
          </Text>
        ) : null}
      </View>
      <Icon name="chevron" size={20} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    padding: 14,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radius.lg,
  },
  pressed: { opacity: 0.85 },
  date: {
    width: 52,
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
    backgroundColor: colors.primarySoft,
  },
  day: { color: colors.primary, fontSize: 22, fontWeight: '700' },
  month: { color: colors.primary, fontSize: fontSize.caption - 1, fontWeight: '500' },
  info: { flex: 1, gap: 6 },
  badges: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 6 },
  name: { color: colors.ink, fontSize: fontSize.body + 1, fontWeight: '600' },
  place: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  meta: { color: colors.muted, fontSize: fontSize.small, flexShrink: 1 },
});
