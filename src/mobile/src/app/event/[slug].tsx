import { useQuery } from '@tanstack/react-query';
import { useLocalSearchParams } from 'expo-router';
import { ActivityIndicator, Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { eventQuery } from '@/api/events';
import { formatDate, statusLabel } from '@/lib/format';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

// Step 4: minimal detail so deep links and navigation work end to end.
// The designed Event Detail screen is built in step 6.
export default function EventDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const query = useQuery(eventQuery(slug));

  if (query.isPending) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (!query.data) {
    return (
      <View style={styles.center}>
        <Text style={styles.muted}>Không tìm thấy giải này.</Text>
      </View>
    );
  }

  const event = query.data;
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{event.name}</Text>
      <Text style={styles.muted}>
        {formatDate(event.start_date)} · {event.province ?? 'Việt Nam'} · {statusLabel(event.status)}
      </Text>
      {event.distances.map((distance) => (
        <Text key={distance.label} style={styles.body}>
          {distance.label}
        </Text>
      ))}
      {event.registration_url ? (
        <Pressable
          accessibilityRole="link"
          onPress={() => Linking.openURL(event.registration_url!)}
          style={styles.cta}
        >
          <Text style={styles.ctaText}>Đăng ký trên trang ban tổ chức</Text>
        </Pressable>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  container: { padding: spacing.lg, gap: spacing.md },
  title: { color: colors.ink, fontSize: fontSize.large, fontWeight: '700' },
  muted: { color: colors.muted, fontSize: fontSize.body },
  body: { color: colors.ink, fontSize: fontSize.body },
  cta: { backgroundColor: colors.primary, borderRadius: radius.pill, padding: spacing.lg, alignItems: 'center' },
  ctaText: { color: colors.onPrimary, fontWeight: '600', fontSize: fontSize.body },
});
