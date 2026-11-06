import { useInfiniteQuery } from '@tanstack/react-query';
import { Link } from 'expo-router';
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { eventsQuery } from '@/api/events';
import { formatDate, statusLabel } from '@/lib/format';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

// Step 4: a plain list that proves the app talks to the API. The designed
// Event List screen (search, chips, cards) is built in step 5.
export default function EventListScreen() {
  const query = useInfiniteQuery(eventsQuery({}));
  const items = query.data?.pages.flatMap((page) => page.items) ?? [];

  if (query.isPending) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (query.isError && items.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.message}>Không tải được danh sách giải.</Text>
        <Pressable accessibilityRole="button" onPress={() => query.refetch()} style={styles.retry}>
          <Text style={styles.retryText}>Thử lại</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.slug}
      contentContainerStyle={styles.list}
      onEndReached={() => query.hasNextPage && query.fetchNextPage()}
      refreshControl={<RefreshControl refreshing={query.isRefetching} onRefresh={() => void query.refetch()} />}
      ListEmptyComponent={<Text style={styles.message}>Chưa có giải nào.</Text>}
      renderItem={({ item }) => (
        <Link href={{ pathname: '/event/[slug]', params: { slug: item.slug } }} asChild>
          <Pressable accessibilityRole="button" style={styles.row}>
            <Text style={styles.name}>{item.name}</Text>
            <Text style={styles.meta}>
              {formatDate(item.start_date)} · {item.province ?? 'Việt Nam'} · {statusLabel(item.status)}
            </Text>
          </Pressable>
        </Link>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, gap: spacing.md },
  list: { padding: spacing.lg, gap: spacing.md },
  row: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: spacing.lg,
    gap: spacing.xs,
  },
  name: { color: colors.ink, fontSize: fontSize.body + 1, fontWeight: '600' },
  meta: { color: colors.muted, fontSize: fontSize.small },
  message: { color: colors.muted, fontSize: fontSize.body, textAlign: 'center' },
  retry: { backgroundColor: colors.primary, borderRadius: radius.pill, paddingHorizontal: spacing.xl, paddingVertical: spacing.md },
  retryText: { color: colors.onPrimary, fontWeight: '600' },
});
