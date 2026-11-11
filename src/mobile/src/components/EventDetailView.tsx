import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { EventDetail } from '@/api/events';
import { Badge } from '@/components/Badge';
import { Icon, type IconName } from '@/components/Icon';
import {
  deadlineLines,
  distanceDetails,
  eventDateLine,
  formatDate,
  isHttpUrl,
  mapSearchUrl,
  statusBadge,
  typeLabel,
} from '@/lib/format';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface Props {
  event: EventDetail;
  bottomInset?: number;
  onOpenUrl: (url: string) => void;
  onOpenAbout?: () => void;
}

const NOTICES: Record<string, { text: string; bg: string; fg: string }> = {
  cancelled: { text: 'Giải đã bị hủy.', bg: colors.dangerSoft, fg: colors.danger },
  postponed: {
    text: 'Giải bị hoãn. Hãy xem trang ban tổ chức để biết thời gian mới.',
    bg: colors.warnSoft,
    fg: colors.warn,
  },
  completed: { text: 'Giải đã diễn ra.', bg: colors.bg, fg: colors.muted },
};

export function EventDetailView({ event, bottomInset = 0, onOpenUrl, onOpenAbout }: Props) {
  const status = statusBadge(event);
  const typeTone = event.event_type === 'trail' ? 'trail' : event.event_type === 'road' ? 'road' : 'muted';
  const startTimes = event.distances.map((d) => d.start_time).filter((t): t is string => Boolean(t)).sort();
  const place = [event.venue, event.province].filter(Boolean).join(', ');
  const mapUrl = isHttpUrl(event.map_url) ? event.map_url : mapSearchUrl(event.venue, event.province);
  const deadline = deadlineLines(event.registration_deadline, event.days_left, event.status);
  const notice = NOTICES[event.status];

  const link = isHttpUrl(event.registration_url) ? event.registration_url : null;
  const sourceLink = isHttpUrl(event.source_url) ? event.source_url : null;
  const canRegister = event.status === 'registration_open' && link !== null;
  const showLink = !['cancelled', 'completed'].includes(event.status);
  const target = link ?? sourceLink;
  const verifiedText = event.last_verified_at
    ? `Kiểm tra lần cuối ${formatDate(event.last_verified_at.slice(0, 10))}.`
    : 'Chưa được kiểm chứng với trang ban tổ chức.';

  return (
    <View style={styles.root}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.badges}>
          <Badge label={typeLabel(event.event_type)} tone={typeTone} />
          <Badge label={status.label} tone={status.tone} />
        </View>
        <Text accessibilityRole="header" style={styles.title}>
          {event.name}
        </Text>

        {notice ? (
          <View style={[styles.notice, { backgroundColor: notice.bg }]} accessibilityRole="alert">
            <Text style={[styles.noticeText, { color: notice.fg }]}>{notice.text}</Text>
          </View>
        ) : null}

        <InfoRow icon="calendar" text={eventDateLine(event.start_date, event.end_date, startTimes[0])} />
        {place ? (
          <InfoRow
            icon="pin"
            text={place}
            link={mapUrl ? { label: 'Xem bản đồ', onPress: () => onOpenUrl(mapUrl) } : undefined}
          />
        ) : null}
        {event.organizer ? <InfoRow icon="info" text={`Ban tổ chức: ${event.organizer}`} /> : null}

        {deadline ? (
          <View style={styles.deadline}>
            <Icon name="clock" size={20} color={colors.primary} />
            <View style={styles.flex}>
              <Text style={styles.deadlineTitle}>{deadline.title}</Text>
              <Text style={styles.deadlineSub}>{deadline.sub}</Text>
            </View>
          </View>
        ) : null}

        {event.distances.length > 0 ? (
          <View style={styles.section}>
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Cự ly
            </Text>
            {event.distances.map((d) => {
              const details = distanceDetails(d);
              return (
                <View key={d.label} style={styles.distance} accessible accessibilityLabel={`${d.label}. ${details.primary}. ${details.secondary}`}>
                  <Text style={styles.distanceLabel}>{d.label}</Text>
                  <View style={styles.flex}>
                    {details.primary ? <Text style={styles.distancePrimary}>{details.primary}</Text> : null}
                    {details.secondary ? <Text style={styles.distanceSecondary}>{details.secondary}</Text> : null}
                    {!details.primary && !details.secondary ? (
                      <Text style={styles.distanceSecondary}>Chưa có thông tin chi tiết</Text>
                    ) : null}
                  </View>
                </View>
              );
            })}
          </View>
        ) : null}

        <View style={styles.source}>
          <Icon name="info" size={16} />
          <Text style={styles.sourceText}>
            {event.source_name ? `Nguồn: ${event.source_name}. ` : ''}
            {verifiedText} Thông tin có thể thay đổi, hãy xác nhận trên trang ban tổ chức.
            {onOpenAbout ? (
              <Text accessibilityRole="link" style={styles.aboutLink} onPress={onOpenAbout}>
                {' '}
                Về dữ liệu
              </Text>
            ) : null}
          </Text>
        </View>
      </ScrollView>

      {showLink && target ? (
        <View style={[styles.bottom, { paddingBottom: Math.max(bottomInset, spacing.lg) }]}>
          <Pressable
            accessibilityRole="link"
            accessibilityLabel={canRegister ? 'Đăng ký trên trang ban tổ chức' : 'Xem trang ban tổ chức'}
            onPress={() => onOpenUrl(target)}
            style={({ pressed }) => [styles.cta, !canRegister && styles.ctaSecondary, pressed && styles.pressed]}
          >
            <Text style={[styles.ctaText, !canRegister && styles.ctaTextSecondary]}>
              {canRegister ? 'Đăng ký trên trang ban tổ chức' : link ? 'Xem trang ban tổ chức' : 'Xem trang nguồn'}
            </Text>
            <Icon name="external" size={18} color={canRegister ? colors.onPrimary : colors.primary} />
          </Pressable>
          <Text style={styles.caption}>
            {link ? 'Mở trang của ban tổ chức trong trình duyệt' : 'Mở trang nguồn trong trình duyệt'}
          </Text>
        </View>
      ) : null}
    </View>
  );
}

function InfoRow({
  icon,
  text,
  link,
}: {
  icon: IconName;
  text: string;
  link?: { label: string; onPress: () => void };
}) {
  return (
    <View style={styles.infoRow}>
      <Icon name={icon} size={20} />
      <View style={styles.flex}>
        <Text style={styles.infoText}>{text}</Text>
        {link ? (
          <Pressable accessibilityRole="link" onPress={link.onPress} hitSlop={8}>
            <Text style={styles.infoLink}>{link.label}</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1, gap: 2 },
  content: { padding: spacing.lg, gap: 14 },
  badges: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  title: { color: colors.ink, fontSize: fontSize.large, fontWeight: '700' },
  notice: { borderRadius: radius.md, padding: spacing.md },
  noticeText: { fontSize: fontSize.body, fontWeight: '600' },
  infoRow: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  infoText: { color: colors.ink, fontSize: fontSize.body, fontWeight: '500' },
  infoLink: { color: colors.primary, fontSize: fontSize.small, fontWeight: '500', paddingVertical: 2 },
  deadline: {
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.primarySoft,
  },
  deadlineTitle: { color: colors.ink, fontSize: fontSize.body - 1, fontWeight: '600' },
  deadlineSub: { color: colors.muted, fontSize: fontSize.small },
  section: { gap: spacing.md },
  sectionTitle: { color: colors.ink, fontSize: 16, fontWeight: '700' },
  distance: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    padding: 14,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  distanceLabel: { color: colors.ink, fontSize: fontSize.title, fontWeight: '700', minWidth: 56 },
  distancePrimary: { color: colors.ink, fontSize: fontSize.small, fontWeight: '500' },
  distanceSecondary: { color: colors.muted, fontSize: fontSize.caption },
  source: { flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start' },
  aboutLink: { color: colors.primary, fontWeight: '600' },
  sourceText: { flex: 1, color: colors.muted, fontSize: fontSize.caption },
  bottom: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    gap: 6,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  cta: {
    minHeight: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  ctaSecondary: { backgroundColor: colors.surface, borderWidth: 1.5, borderColor: colors.primary },
  pressed: { opacity: 0.85 },
  ctaText: { color: colors.onPrimary, fontSize: fontSize.body + 1, fontWeight: '600' },
  ctaTextSecondary: { color: colors.primary },
  caption: { color: colors.muted, fontSize: fontSize.caption, textAlign: 'center' },
});
