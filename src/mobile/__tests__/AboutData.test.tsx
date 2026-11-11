import { render, screen } from '@testing-library/react-native';

import AboutDataScreen from '@/app/about-data';

describe('<AboutDataScreen />', () => {
  it('explains sources, updates, the verified date and the organizer page', async () => {
    await render(<AboutDataScreen />);
    expect(screen.getByRole('header', { name: 'Về dữ liệu' })).toBeTruthy();
    for (const title of ['Dữ liệu đến từ đâu', 'Cập nhật thế nào', 'Luôn xác nhận với ban tổ chức']) {
      expect(screen.getByRole('header', { name: title })).toBeTruthy();
    }
    expect(screen.getByText(/Kiểm tra lần cuối/)).toBeTruthy();
  });
});
