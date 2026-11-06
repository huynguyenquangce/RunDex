import { fireEvent, render, screen } from '@testing-library/react-native';

import type { EventFilters } from '@/api/events';
import { FilterSheet } from '@/features/events/FilterSheet';

const TODAY = new Date(2026, 10, 6);

async function setup(draft: EventFilters = {}, opts: { total?: number; visible?: boolean } = { total: 24 }) {
  const handlers = { onChange: jest.fn(), onApply: jest.fn(), onClear: jest.fn(), onClose: jest.fn() };
  await render(<FilterSheet visible={opts.visible ?? true} draft={draft} total={opts.total} today={TODAY} {...handlers} />);
  return handlers;
}

const isSelected = (label: string) => screen.getByLabelText(label).props.accessibilityState?.selected === true;

describe('<FilterSheet />', () => {
  it('shows every group and the result count on the apply button', async () => {
    await setup();
    for (const title of ['Loại giải', 'Cự ly', 'Thời gian', 'Khu vực']) {
      expect(screen.getByText(title)).toBeTruthy();
    }
    expect(screen.getByText('Xem 24 giải')).toBeTruthy();
    expect(screen.getByText('Chỉ giải còn mở đăng ký')).toBeTruthy();
  });

  it('marks the options of the current draft as selected', async () => {
    await setup({ type: 'trail', distance: ['42', 'ultra'], region: 'south' });
    expect(isSelected('Trail')).toBe(true);
    expect(isSelected('Đường nhựa')).toBe(false);
    expect(isSelected('42K')).toBe(true);
    expect(isSelected('50K+')).toBe(true);
    expect(isSelected('21K')).toBe(false);
    expect(isSelected('Miền Nam')).toBe(true);
    expect(isSelected('Miền Bắc')).toBe(false);
  });

  it('reports each change with the other filters kept', async () => {
    const { onChange } = await setup({ type: 'trail' });
    await fireEvent.press(screen.getByLabelText('21K'));
    expect(onChange).toHaveBeenLastCalledWith({ type: 'trail', distance: ['21'] });
    await fireEvent.press(screen.getByLabelText('Miền Trung'));
    expect(onChange).toHaveBeenLastCalledWith({ type: 'trail', region: 'central' });
    await fireEvent.press(screen.getByLabelText('Trail'));
    expect(onChange).toHaveBeenLastCalledWith({ type: undefined });
    await fireEvent.press(screen.getByLabelText('3 tháng tới'));
    expect(onChange).toHaveBeenLastCalledWith({ type: 'trail', from: '2026-11-06', to: '2027-02-06' });
  });

  it('applies, clears and closes', async () => {
    const { onApply, onClear, onClose } = await setup();
    await fireEvent.press(screen.getByText('Xem 24 giải'));
    await fireEvent.press(screen.getByText('Xóa bộ lọc'));
    await fireEvent.press(screen.getByLabelText('Đóng'));
    expect(onApply).toHaveBeenCalledTimes(1);
    expect(onClear).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('shows a neutral label while the count is loading', async () => {
    await setup({}, { total: undefined });
    expect(screen.getByText('Xem kết quả')).toBeTruthy();
  });

  it('handles zero results', async () => {
    await setup({}, { total: 0 });
    expect(screen.getByText('Xem 0 giải')).toBeTruthy();
  });

  it('renders nothing when closed', async () => {
    await setup({}, { total: 1, visible: false });
    expect(screen.queryByText('Bộ lọc')).toBeNull();
  });
});
