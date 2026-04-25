import { apiGet } from './client';
import {
  summaryResponseSchema,
  topTrendsResponseSchema,
  trendTimeseriesResponseSchema,
} from './schemas';
import type {
  SummaryResponse,
  TopTrendsResponse,
  TrendTimeseriesResponse,
} from './types';

export async function fetchTopTrends(limit?: number): Promise<TopTrendsResponse> {
  const params = limit !== undefined ? `?limit=${limit}` : '';
  const raw = await apiGet<unknown>(`/api/v1/trends/top${params}`);
  return topTrendsResponseSchema.parse(raw);
}

export async function fetchSummary(limit?: number): Promise<SummaryResponse> {
  const params = limit !== undefined ? `?limit=${limit}` : '';
  const raw = await apiGet<unknown>(`/api/v1/summary${params}`);
  return summaryResponseSchema.parse(raw);
}

export async function fetchTimeseries(
  query: string,
  limit?: number,
): Promise<TrendTimeseriesResponse> {
  const base = `/api/v1/trends/${encodeURIComponent(query)}/timeseries`;
  const params = limit !== undefined ? `?limit=${limit}` : '';
  const raw = await apiGet<unknown>(`${base}${params}`);
  return trendTimeseriesResponseSchema.parse(raw);
}
