import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { CACHE_BUSTER, DAY_MS, persister, queryClient } from '@/api/queryClient';
import { colors } from '@/theme/tokens';

export default function RootLayout() {
  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{ persister, maxAge: DAY_MS, buster: CACHE_BUSTER }}
    >
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.bg },
          headerTintColor: colors.ink,
          headerShadowVisible: false,
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="about-data" options={{ title: 'Về dữ liệu', headerBackTitle: 'Giải chạy' }} />
        <Stack.Screen name="event/[slug]" options={{ title: 'Chi tiết giải', headerBackTitle: 'Giải chạy' }} />
      </Stack>
    </PersistQueryClientProvider>
  );
}
