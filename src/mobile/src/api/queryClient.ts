import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import { QueryClient, onlineManager } from '@tanstack/react-query';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

export const DAY_MS = 24 * 60 * 60 * 1000;

// Keep the last successful responses on the device so the list still opens offline.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, gcTime: DAY_MS, retry: 2 },
  },
});

export const persister = createAsyncStoragePersister({
  storage: AsyncStorage,
  key: 'rundex-query-cache',
  throttleTime: 1000,
});

// Bump when the cached response shape changes to drop old caches.
export const CACHE_BUSTER = 'v1';

onlineManager.setEventListener((setOnline) =>
  NetInfo.addEventListener((state) => setOnline(state.isConnected !== false)),
);
