import type { ReactElement } from 'react';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import { colors } from '@/theme/tokens';

// Same 24x24 stroke icons as the Figma design.
const ICONS: Record<string, ReactElement> = {
  search: (
    <>
      <Circle cx="11" cy="11" r="7" />
      <Path d="m20 20-3.5-3.5" />
    </>
  ),
  chevron: <Path d="m9 18 6-6-6-6" />,
  pin: (
    <>
      <Path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" />
      <Circle cx="12" cy="10" r="2.5" />
    </>
  ),
  filter: <Path d="M4 6h16M7 12h10M10 18h4" />,
  close: <Path d="M6 6l12 12M18 6 6 18" />,
  calendar: (
    <>
      <Rect x="3" y="5" width="18" height="16" rx="2" />
      <Path d="M16 3v4M8 3v4M3 10h18" />
    </>
  ),
  cloudOff: <Path d="M3 3l18 18M9 5a6 6 0 0 1 10 4h1a4 4 0 0 1 2 7M6 9a5 5 0 0 0-1 10h11" />,
};

export type IconName = keyof typeof ICONS;

interface Props {
  name: IconName;
  size?: number;
  color?: string;
}

export function Icon({ name, size = 20, color = colors.muted }: Props) {
  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {ICONS[name]}
    </Svg>
  );
}
