import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

const SECTIONS: { icon: IconName; title: string; body: string }[] = [
  {
    icon: 'search',
    title: 'Dữ liệu đến từ đâu',
    body:
      'Trang chính thức của ban tổ chức, cổng đăng ký và bán vé (ví dụ pace8.vn), và một số trang tin chạy bộ ' +
      'để phát hiện giải mới. RunDex chỉ lấy dữ kiện (tên, ngày, địa điểm, cự ly, phí) và dẫn bạn về trang đăng ký ' +
      'của ban tổ chức. Không sao chép mô tả hay hình ảnh.',
  },
  {
    icon: 'clock',
    title: 'Cập nhật thế nào',
    body:
      'Hệ thống tự kiểm tra các nguồn theo lịch và tìm giải mới. Thay đổi quan trọng như ngày, địa điểm, ' +
      'trạng thái hoặc liên kết đăng ký luôn được một người xem lại trước khi hiển thị.',
  },
  {
    icon: 'calendar',
    title: '"Kiểm tra lần cuối" nghĩa là gì',
    body:
      'Lần gần nhất thông tin của giải được đối chiếu với nguồn đáng tin cậy hoặc được người quản trị xác nhận. ' +
      'Nếu chưa có ngày này, giải mới chỉ thấy ở nguồn tham khảo và chưa được kiểm chứng.',
  },
  {
    icon: 'external',
    title: 'Luôn xác nhận với ban tổ chức',
    body:
      'Giờ xuất phát, thời gian cắt, phí và hạn đăng ký có thể đổi. Trước khi đăng ký, hãy kiểm tra lại trên ' +
      'trang của ban tổ chức. Nếu bạn là ban tổ chức và muốn gỡ hoặc sửa thông tin, hãy liên hệ để chúng tôi xử lý.',
  },
];

export default function AboutDataScreen() {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text accessibilityRole="header" style={styles.title}>
        Về dữ liệu
      </Text>
      <Text style={styles.lead}>RunDex là công cụ tra cứu. Việc đăng ký diễn ra trên trang của ban tổ chức.</Text>
      {SECTIONS.map((section) => (
        <View key={section.title} style={styles.card}>
          <View style={styles.iconWrap}>
            <Icon name={section.icon} size={20} color={colors.primary} />
          </View>
          <View style={styles.cardText}>
            <Text accessibilityRole="header" style={styles.cardTitle}>
              {section.title}
            </Text>
            <Text style={styles.cardBody}>{section.body}</Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, gap: spacing.md },
  title: { color: colors.ink, fontSize: fontSize.large, fontWeight: '700' },
  lead: { color: colors.muted, fontSize: fontSize.body, marginBottom: spacing.xs },
  card: {
    flexDirection: 'row',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: radius.md,
    backgroundColor: colors.primarySoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardText: { flex: 1, gap: spacing.xs },
  cardTitle: { color: colors.ink, fontSize: fontSize.body, fontWeight: '600' },
  cardBody: { color: colors.muted, fontSize: fontSize.small, lineHeight: 20 },
});
