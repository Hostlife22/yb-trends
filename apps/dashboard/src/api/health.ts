import { apiGet } from './client';
import { healthResponseSchema, readyResponseSchema } from './schemas';
import type { HealthResponse, ReadyResponse } from './types';

export async function fetchHealth(): Promise<HealthResponse> {
  const raw = await apiGet<unknown>('/health');
  return healthResponseSchema.parse(raw);
}

export async function fetchReady(): Promise<ReadyResponse> {
  const raw = await apiGet<unknown>('/ready');
  return readyResponseSchema.parse(raw);
}
