import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

export function SkeletonCards({ count = 5 }: { count?: number }) {
  return (
    <View style={styles.stack} accessibilityLabel="Đang tải danh sách giải">
      {Array.from({ length: count }, (_, i) => (
        <View key={i} style={styles.skeleton} />
      ))}
    </View>
  );
}

interface MessageProps {
  title: string;
  body?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function Message({ title, body, actionLabel, onAction }: MessageProps) {
  return (
    <View style={styles.message}>
      <Text style={styles.title}>{title}</Text>
      {body ? <Text style={styles.body}>{body}</Text> : null}
      {actionLabel && onAction ? (
        <Pressable accessibilityRole="button" onPress={onAction} style={styles.action}>
          <Text style={styles.actionText}>{actionLabel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

export function OfflineBanner() {
  return (
    <View style={styles.banner} accessibilityRole="alert">
      <Icon name="cloudOff" size={16} color={colors.surface} />
      <Text style={styles.bannerText}>Ngoại tuyến · hiển thị dữ liệu đã lưu trên máy</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  stack: { gap: spacing.md },
  skeleton: { height: 116, borderRadius: radius.lg, backgroundColor: colors.border, opacity: 0.6 },
  message: { alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xxl, paddingHorizontal: spacing.xl },
  title: { color: colors.ink, fontSize: fontSize.title - 2, fontWeight: '700', textAlign: 'center' },
  body: { color: colors.muted, fontSize: fontSize.body, textAlign: 'center' },
  action: {
    marginTop: spacing.sm,
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  actionText: { color: colors.onPrimary, fontWeight: '600', fontSize: fontSize.body },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    backgroundColor: colors.ink,
  },
  bannerText: { color: colors.surface, fontSize: fontSize.small },
});
