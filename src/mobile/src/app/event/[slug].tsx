import { useQuery } from '@tanstack/react-query';
import { useLocalSearchParams } from 'expo-router';
import { Alert, Linking, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ApiError } from '@/api/client';
import { eventQuery } from '@/api/events';
import { EventDetailView } from '@/components/EventDetailView';
import { Message, SkeletonCards } from '@/components/ListStates';
import { isHttpUrl } from '@/lib/format';
import { colors, spacing } from '@/theme/tokens';

export default function EventDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const insets = useSafeAreaInsets();
  const query = useQuery(eventQuery(slug));

  const openUrl = (url: string) => {
    if (!isHttpUrl(url)) return;
    Linking.openURL(url).catch(() =>
      Alert.alert('Không mở được liên kết', 'Hãy thử lại hoặc mở trang ban tổ chức bằng trình duyệt.'),
    );
  };

  if (query.data) {
    return <EventDetailView event={query.data} bottomInset={insets.bottom} onOpenUrl={openUrl} />;
  }
  if (query.isPending) {
    return (
      <View style={styles.padded}>
        <SkeletonCards count={3} />
      </View>
    );
  }
  const notFound = query.error instanceof ApiError && query.error.status === 404;
  return (
    <View style={styles.center}>
      <Message
        title={notFound ? 'Không tìm thấy giải này' : 'Không tải được thông tin giải'}
        body={notFound ? 'Giải có thể đã bị gỡ khỏi danh sách.' : 'Kiểm tra kết nối mạng rồi thử lại.'}
        actionLabel={notFound ? undefined : 'Thử lại'}
        onAction={notFound ? undefined : () => void query.refetch()}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  padded: { flex: 1, padding: spacing.lg, backgroundColor: colors.bg },
  center: { flex: 1, justifyContent: 'center', backgroundColor: colors.bg },
});
