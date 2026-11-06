import { infiniteQueryOptions, queryOptions } from '@tanstack/react-query';

import { ApiError, api } from './client';
import type { components, paths } from './schema';

export type EventSummary = components['schemas']['EventSummary'];
export type EventDetail = components['schemas']['EventDetail'];
export type EventPage = components['schemas']['EventPage'];

type ListQuery = NonNullable<paths['/v1/events']['get']['parameters']['query']>;
export type EventType = NonNullable<ListQuery['type']>;
export type DistanceBucket = NonNullable<ListQuery['distance']>[number];
export type Region = NonNullable<ListQuery['region']>;

/** Filters as the UI thinks about them; mapped to API query parameters below. */
export interface EventFilters {
  q?: string;
  type?: EventType;
  distance?: DistanceBucket[];
  region?: Region;
  from?: string;
  to?: string;
  openOnly?: boolean;
  includePast?: boolean;
}

export const PAGE_SIZE = 20;

export function toQueryParams(
  filters: EventFilters,
  cursor?: string,
  limit: number = PAGE_SIZE,
): ListQuery {
  return {
    q: filters.q?.trim() || undefined,
    type: filters.type,
    distance: filters.distance?.length ? filters.distance : undefined,
    region: filters.region,
    from: filters.from,
    to: filters.to,
    open_only: filters.openOnly || undefined,
    include_past: filters.includePast || undefined,
    limit,
    cursor,
  };
}

export const eventsQuery = (filters: EventFilters) =>
  infiniteQueryOptions({
    queryKey: ['events', filters] as const,
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam, signal }) => {
      const { data, response } = await api.GET('/v1/events', {
        params: { query: toQueryParams(filters, pageParam) },
        signal,
      });
      if (!data) throw new ApiError(response.status, 'Could not load events');
      return data;
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });

/** How many events match the filters (one tiny request); feeds the filter sheet button. */
export const countQuery = (filters: EventFilters) =>
  queryOptions({
    queryKey: ['events-count', filters] as const,
    queryFn: async ({ signal }) => {
      const { data, response } = await api.GET('/v1/events', {
        params: { query: toQueryParams(filters, undefined, 1) },
        signal,
      });
      if (!data) throw new ApiError(response.status, 'Could not count events');
      return data.total;
    },
  });

export const eventQuery = (slug: string) =>
  queryOptions({
    queryKey: ['event', slug] as const,
    queryFn: async ({ signal }) => {
      const { data, response } = await api.GET('/v1/events/{slug}', {
        params: { path: { slug } },
        signal,
      });
      if (!data) throw new ApiError(response.status, 'Could not load event');
      return data;
    },
  });
