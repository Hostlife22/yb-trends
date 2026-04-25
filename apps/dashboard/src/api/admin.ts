import { apiGet, apiPost } from './client';
import {
  alertsResponseSchema,
  metricsResponseSchema,
  snapshotsResponseSchema,
  syncResponseSchema,
  syncRunsResponseSchema,
} from './schemas';
import type {
  AlertsResponse,
  MetricsResponse,
  SnapshotsResponse,
  SyncResponse,
  SyncRunsResponse,
} from './types';

export async function fetchMetrics(): Promise<MetricsResponse> {
  const raw = await apiGet<unknown>('/api/v1/admin/metrics');
  return metricsResponseSchema.parse(raw);
}

export async function fetchAlerts(): Promise<AlertsResponse> {
  const raw = await apiGet<unknown>('/api/v1/admin/alerts');
  return alertsResponseSchema.parse(raw);
}

export async function fetchSyncRuns(limit?: number): Promise<SyncRunsResponse> {
  const params = limit !== undefined ? `?limit=${limit}` : '';
  const raw = await apiGet<unknown>(`/api/v1/admin/sync-runs${params}`);
  return syncRunsResponseSchema.parse(raw);
}

export async function fetchSnapshots(limit?: number): Promise<SnapshotsResponse> {
  const params = limit !== undefined ? `?limit=${limit}` : '';
  const raw = await apiGet<unknown>(`/api/v1/admin/snapshots${params}`);
  return snapshotsResponseSchema.parse(raw);
}

export async function triggerSync(
  region?: string,
  period?: string,
): Promise<SyncResponse> {
  const searchParams = new URLSearchParams();
  if (region !== undefined) searchParams.set('region', region);
  if (period !== undefined) searchParams.set('period', period);
  const query = searchParams.toString();
  const path = `/api/v1/admin/sync${query ? `?${query}` : ''}`;
  const raw = await apiPost<unknown>(path);
  return syncResponseSchema.parse(raw);
}
