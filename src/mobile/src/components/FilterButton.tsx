import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { colors, radius } from '@/theme/tokens';

interface Props {
  count: number;
  onPress: () => void;
}

export function FilterButton({ count, onPress }: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={count > 0 ? `Bộ lọc, đang dùng ${count} nhóm` : 'Bộ lọc'}
      onPress={onPress}
      style={({ pressed }) => [styles.button, pressed && styles.pressed]}
    >
      <Icon name="filter" size={20} color={colors.ink} />
      {count > 0 ? (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{count}</Text>
        </View>
      ) : null}
    </Pressable>
  );
}

const SIZE = Platform.OS === 'ios' ? 44 : 52;

const styles = StyleSheet.create({
  button: {
    width: SIZE,
    height: SIZE,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: Platform.OS === 'ios' ? radius.md : SIZE / 2,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  pressed: { opacity: 0.8 },
  badge: {
    position: 'absolute',
    top: -6,
    right: -6,
    minWidth: 18,
    height: 18,
    paddingHorizontal: 4,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 9,
    backgroundColor: colors.primary,
  },
  badgeText: { color: colors.onPrimary, fontSize: 11, fontWeight: '700' },
});
