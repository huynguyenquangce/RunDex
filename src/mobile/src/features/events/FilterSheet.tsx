import { type ReactNode } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';

import type { EventFilters } from '@/api/events';
import { FilterChip } from '@/components/FilterChip';
import { Icon } from '@/components/Icon';
import {
  DISTANCE_OPTIONS,
  REGION_OPTIONS,
  TIME_OPTIONS,
  TYPE_OPTIONS,
  activeTime,
  setOpenOnly,
  setRegion,
  setTime,
  setType,
  toggleDistance,
} from '@/features/events/filters';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface Props {
  visible: boolean;
  draft: EventFilters;
  /** Events matching the draft (undefined while it loads). */
  total: number | undefined;
  today: Date;
  onChange: (next: EventFilters) => void;
  onApply: () => void;
  onClear: () => void;
  onClose: () => void;
}

export function FilterSheet({ visible, draft, total, today, onChange, onApply, onClear, onClose }: Props) {
  const time = activeTime(draft, today);
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View style={styles.root}>
        <Pressable accessibilityLabel="Đóng bộ lọc" accessibilityRole="button" style={styles.scrim} onPress={onClose} />
        <View style={styles.sheet} accessibilityViewIsModal>
          <View style={styles.grabber} />
          <View style={styles.header}>
            <Text accessibilityRole="header" style={styles.title}>
              Bộ lọc
            </Text>
            <Pressable accessibilityRole="button" accessibilityLabel="Đóng" hitSlop={12} onPress={onClose}>
              <Icon name="close" size={22} color={colors.ink} />
            </Pressable>
          </View>

          <ScrollView style={styles.body} contentContainerStyle={styles.groups}>
            <Group title="Loại giải">
              <FilterChip label="Tất cả" selected={!draft.type} onPress={() => onChange(setType(draft, undefined))} />
              {TYPE_OPTIONS.map((o) => (
                <FilterChip
                  key={o.id}
                  label={o.label}
                  selected={draft.type === o.id}
                  onPress={() => onChange(setType(draft, draft.type === o.id ? undefined : o.id))}
                />
              ))}
            </Group>
            <Group title="Cự ly">
              {DISTANCE_OPTIONS.map((o) => (
                <FilterChip
                  key={o.id}
                  label={o.label}
                  selected={Boolean(draft.distance?.includes(o.id))}
                  onPress={() => onChange(toggleDistance(draft, o.id))}
                />
              ))}
            </Group>
            <Group title="Thời gian">
              {TIME_OPTIONS.map((o) => (
                <FilterChip
                  key={o.id}
                  label={o.label}
                  selected={time === o.id}
                  onPress={() => onChange(setTime(draft, time === o.id ? undefined : o.id, today))}
                />
              ))}
            </Group>
            <Group title="Khu vực">
              {REGION_OPTIONS.map((o) => (
                <FilterChip
                  key={o.id}
                  label={o.label}
                  selected={draft.region === o.id}
                  onPress={() => onChange(setRegion(draft, draft.region === o.id ? undefined : o.id))}
                />
              ))}
            </Group>
            <View style={styles.switchRow}>
              <Text style={styles.switchLabel}>Chỉ giải còn mở đăng ký</Text>
              <Switch
                accessibilityLabel="Chỉ giải còn mở đăng ký"
                value={Boolean(draft.openOnly)}
                onValueChange={(value) => onChange(setOpenOnly(draft, value))}
                trackColor={{ true: colors.primary, false: colors.border }}
              />
            </View>
          </ScrollView>

          <View style={styles.footer}>
            <Pressable accessibilityRole="button" onPress={onClear} style={styles.clear}>
              <Text style={styles.clearText}>Xóa bộ lọc</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={onApply}
              style={({ pressed }) => [styles.apply, pressed && styles.pressed]}
            >
              <Text style={styles.applyText}>{total === undefined ? 'Xem kết quả' : `Xem ${total} giải`}</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={styles.group}>
      <Text accessibilityRole="header" style={styles.groupTitle}>
        {title}
      </Text>
      <View style={styles.options}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, justifyContent: 'flex-end' },
  scrim: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.4)' },
  sheet: {
    maxHeight: '88%',
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xl,
  },
  grabber: { alignSelf: 'center', width: 36, height: 4, borderRadius: 2, backgroundColor: colors.border },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  title: { color: colors.ink, fontSize: fontSize.title, fontWeight: '700' },
  body: { flexGrow: 0 },
  groups: { paddingHorizontal: spacing.lg, gap: spacing.lg, paddingBottom: spacing.md },
  group: { gap: spacing.sm },
  groupTitle: { color: colors.ink, fontSize: fontSize.body - 1, fontWeight: '600' },
  options: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  switchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', minHeight: 44 },
  switchLabel: { color: colors.ink, fontSize: fontSize.body, fontWeight: '500', flex: 1 },
  footer: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.lg, paddingTop: spacing.sm },
  clear: { minHeight: 52, justifyContent: 'center', paddingHorizontal: spacing.lg },
  clearText: { color: colors.ink, fontSize: fontSize.body, fontWeight: '600' },
  apply: {
    flex: 1,
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  pressed: { opacity: 0.85 },
  applyText: { color: colors.onPrimary, fontSize: fontSize.body + 1, fontWeight: '600' },
});
