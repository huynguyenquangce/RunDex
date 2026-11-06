import { apiBaseUrl } from '@/api/config';

describe('apiBaseUrl', () => {
  it('prefers EXPO_PUBLIC_API_URL and trims trailing slashes', () => {
    expect(apiBaseUrl('http://192.168.1.20:8000//', 'ios')).toBe('http://192.168.1.20:8000');
  });

  it('uses the host loopback alias on the Android emulator', () => {
    expect(apiBaseUrl(undefined, 'android')).toBe('http://10.0.2.2:8000');
  });

  it('uses localhost on iOS', () => {
    expect(apiBaseUrl(undefined, 'ios')).toBe('http://localhost:8000');
  });
});
