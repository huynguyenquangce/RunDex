import { Platform, Pressable, StyleSheet, TextInput, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface Props {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
}

export function SearchField({ value, onChangeText, placeholder = 'Tìm giải, địa điểm' }: Props) {
  return (
    <View style={styles.field}>
      <Icon name="search" size={18} />
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        accessibilityLabel="Tìm giải chạy"
        returnKeyType="search"
        autoCorrect={false}
        autoCapitalize="none"
        style={styles.input}
      />
      {value.length > 0 ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Xóa nội dung tìm kiếm"
          hitSlop={12}
          onPress={() => onChangeText('')}
        >
          <Icon name="close" size={18} />
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: 14,
    height: Platform.OS === 'ios' ? 44 : 52,
    borderRadius: Platform.OS === 'ios' ? radius.md : 28,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  input: { flex: 1, color: colors.ink, fontSize: fontSize.body, padding: 0 },
});
