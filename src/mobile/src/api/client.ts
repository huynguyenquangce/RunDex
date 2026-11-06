import createClient from 'openapi-fetch';

import { apiBaseUrl } from './config';
import type { paths } from './schema';

export const api = createClient<paths>({ baseUrl: apiBaseUrl() });

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
