import { useNetInfo } from '@react-native-community/netinfo';
import { keepPreviousData, useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import { FlatList, Platform, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { type EventFilters, countQuery, eventsQuery } from '@/api/events';
import { EventCard } from '@/components/EventCard';
import { Icon } from '@/components/Icon';
import { FilterButton } from '@/components/FilterButton';
import { FilterChip } from '@/components/FilterChip';
import { Message, OfflineBanner, SkeletonCards } from '@/components/ListStates';
import { SearchField } from '@/components/SearchField';
import { withMonthHeaders } from '@/features/events/rows';
import { FilterSheet } from '@/features/events/FilterSheet';
import { CHIPS, activeFilterCount, hasChipFilters, isChipActive, toggleChip } from '@/features/events/filters';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { colors, fontSize, spacing } from '@/theme/tokens';

export default function EventListScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const netInfo = useNetInfo();
  const [text, setText] = useState('');
  const q = useDebouncedValue(text, 300);
  const [chipFilters, setChipFilters] = useState<EventFilters>({});
  const [sheetOpen, setSheetOpen] = useState(false);
  const [draft, setDraft] = useState<EventFilters>({});
  const filters = useMemo<EventFilters>(() => ({ ...chipFilters, q }), [chipFilters, q]);
  const today = useMemo(() => new Date(), []);

  const query = useInfiniteQuery({ ...eventsQuery(filters), placeholderData: keepPreviousData });
  const items = query.data?.pages.flatMap((page) => page.items) ?? [];
  const rows = useMemo(() => withMonthHeaders(items), [items]);
  const hasFilters = Boolean(q.trim()) || hasChipFilters(chipFilters);
  const draftCount = useQuery({ ...countQuery({ ...draft, q }), enabled: sheetOpen, placeholderData: keepPreviousData });
  const offline = netInfo.isConnected === false;

  const clearAll = () => {
    setText('');
    setChipFilters({});
  };

  const aboutButton = (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Về dữ liệu"
      hitSlop={10}
      onPress={() => router.push('/about-data')}
      style={styles.aboutButton}
    >
      <Icon name="info" size={22} />
    </Pressable>
  );

  const header = (
    <View>
      {Platform.OS === 'ios' ? (
        <View style={styles.largeTitle}>
          <Text accessibilityRole="header" style={styles.titleIos}>
            Giải chạy
          </Text>
          <Text style={styles.subtitle}>Tất cả giải chạy tại Việt Nam</Text>
          {aboutButton}
        </View>
      ) : (
        <View style={styles.appBar}>
          <Text accessibilityRole="header" style={styles.titleAndroid}>
            RunDex
          </Text>
          {aboutButton}
        </View>
      )}
      <View style={styles.searchRow}>
        <View style={styles.flex}>
          <SearchField value={text} onChangeText={setText} />
        </View>
        <FilterButton
          count={activeFilterCount(chipFilters)}
          onPress={() => {
            setDraft(chipFilters);
            setSheetOpen(true);
          }}
        />
      </View>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={styles.chips}
      >
        {CHIPS.map((chip) => (
          <FilterChip
            key={chip.id}
            label={chip.label}
            selected={isChipActive(chipFilters, chip.id, today)}
            onPress={() => setChipFilters((current) => toggleChip(current, chip.id, today))}
          />
        ))}
      </ScrollView>
      <View style={styles.listHeader}>
        <Text style={styles.listHeaderLeft}>
          {query.data ? `Sắp diễn ra · ${query.data.pages[0].total} giải` : 'Sắp diễn ra'}
        </Text>
        <Text style={styles.listHeaderRight}>Ngày gần nhất</Text>
      </View>
    </View>
  );

  let empty: React.JSX.Element | undefined;
  if (query.isPending) empty = <SkeletonCards />;
  else if (query.isError && items.length === 0)
    empty = (
      <Message
        title="Không tải được danh sách giải"
        body="Kiểm tra kết nối mạng rồi thử lại."
        actionLabel="Thử lại"
        onAction={() => query.refetch()}
      />
    );
  else if (items.length === 0)
    empty = (
      <Message
        title="Không có giải nào khớp"
        body={hasFilters ? 'Thử bỏ bớt bộ lọc hoặc đổi từ khóa.' : 'Chưa có giải nào sắp diễn ra.'}
        actionLabel={hasFilters ? 'Xóa bộ lọc' : undefined}
        onAction={hasFilters ? clearAll : undefined}
      />
    );

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      {offline ? <OfflineBanner /> : null}
      <FilterSheet
        visible={sheetOpen}
        draft={draft}
        total={draftCount.data}
        today={today}
        onChange={setDraft}
        onClear={() => setDraft({})}
        onClose={() => setSheetOpen(false)}
        onApply={() => {
          setChipFilters(draft);
          setSheetOpen(false);
        }}
      />
      <FlatList
        data={rows}
        keyExtractor={(row) => row.key}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
        contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + spacing.xl }]}
        ListHeaderComponent={header}
        ListEmptyComponent={empty}
        onEndReached={() => {
          if (query.hasNextPage && !query.isFetchingNextPage) void query.fetchNextPage();
        }}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl refreshing={query.isRefetching && !query.isFetchingNextPage} onRefresh={() => void query.refetch()} />
        }
        renderItem={({ item }) =>
          item.kind === 'month' ? (
            <Text accessibilityRole="header" style={styles.monthHeader}>
              {item.label}
            </Text>
          ) : (
            <View style={styles.cardWrap}>
              <EventCard
                event={item.event}
                onPress={() => router.push({ pathname: '/event/[slug]', params: { slug: item.event.slug } })}
              />
            </View>
          )
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  list: { flexGrow: 1 },
  largeTitle: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, paddingBottom: spacing.sm, gap: 2 },
  titleIos: { color: colors.ink, fontSize: fontSize.hero, fontWeight: '700' },
  subtitle: { color: colors.muted, fontSize: fontSize.body },
  appBar: { height: 64, justifyContent: 'center', paddingHorizontal: spacing.lg },
  titleAndroid: { color: colors.ink, fontSize: fontSize.title + 2, fontWeight: '500' },
  flex: { flex: 1 },
  aboutButton: { position: 'absolute', right: spacing.lg, top: Platform.OS === 'ios' ? spacing.md : 21 },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xs,
    paddingBottom: spacing.md,
  },
  chips: { gap: spacing.sm, paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
  },
  listHeaderLeft: { color: colors.muted, fontSize: fontSize.small, fontWeight: '600' },
  listHeaderRight: { color: colors.primary, fontSize: fontSize.small, fontWeight: '500' },
  cardWrap: { paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  monthHeader: {
    color: colors.ink,
    fontSize: fontSize.body,
    fontWeight: '700',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
});
