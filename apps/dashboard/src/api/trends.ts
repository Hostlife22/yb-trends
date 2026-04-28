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

export type TopTrendsFilters = {
  limit?: number;
  language?: string | null;
  country?: string | null;
  minYear?: number | null;
  maxYear?: number | null;
  sortBy?: TopTrendsSort;
};

export type TopTrendsSort =
  | 'final_score'
  | 'search_demand'
  | 'search_momentum'
  | 'youtube_demand'
  | 'youtube_freshness'
  | 'youtube_median_views_14d'
  | 'youtube_total_views_14d';

export async function fetchTopTrends(
  filters: TopTrendsFilters = {},
): Promise<TopTrendsResponse> {
  const search = new URLSearchParams();
  if (filters.limit !== undefined) search.set('limit', String(filters.limit));
  if (filters.language) search.set('language', filters.language);
  if (filters.country) search.set('country', filters.country);
  if (filters.minYear !== undefined && filters.minYear !== null) {
    search.set('min_year', String(filters.minYear));
  }
  if (filters.maxYear !== undefined && filters.maxYear !== null) {
    search.set('max_year', String(filters.maxYear));
  }
  if (filters.sortBy) search.set('sort_by', filters.sortBy);

  const qs = search.toString();
  const url = qs ? `/api/v1/trends/top?${qs}` : '/api/v1/trends/top';
  const raw = await apiGet<unknown>(url);
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
