import { Platform } from 'react-native';

/**
 * Base URL of the RunDex API.
 * - EXPO_PUBLIC_API_URL wins (use your computer's LAN IP on a physical device).
 * - Android emulator reaches the host machine at 10.0.2.2.
 */
export function apiBaseUrl(
  env: string | undefined = process.env.EXPO_PUBLIC_API_URL,
  os: string = Platform.OS,
): string {
  if (env) return env.replace(/\/+$/, '');
  return os === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
}
