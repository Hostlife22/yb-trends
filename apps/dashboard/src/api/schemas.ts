import { z } from 'zod';

export const trendPointSchema = z.object({
  timestamp: z.string(),
  interest: z.number(),
});

export const classifiedTrendItemSchema = z.object({
  query: z.string(),
  title_normalized: z.string(),
  content_type: z.enum(['movie', 'animation', 'unknown']),
  is_movie_or_animation: z.boolean(),
  confidence: z.number(),
  studio: z.string(),
  reason: z.string(),
  interest_level: z.number(),
  growth_velocity: z.number(),
  final_score: z.number(),
});

export const topTrendsResponseSchema = z.object({
  region: z.string(),
  period: z.string(),
  generated_at: z.string(),
  items: z.array(classifiedTrendItemSchema),
});

export const summaryResponseSchema = z.object({
  region: z.string(),
  period: z.string(),
  generated_at: z.string(),
  summary: z.string(),
  top_titles: z.array(z.string()),
});

export const trendTimeseriesResponseSchema = z.object({
  region: z.string(),
  period: z.string(),
  query: z.string(),
  points: z.array(trendPointSchema),
});

export const metricsResponseSchema = z.object({
  region: z.string(),
  period: z.string(),
  latest_snapshot_age_seconds: z.number().nullable(),
  latest_sync_quality_passed: z.boolean().nullable(),
  sync_runs_last_24h: z.number(),
  quality_failures_last_24h: z.number(),
});

export const alertItemSchema = z.object({
  code: z.string(),
  severity: z.enum(['warning', 'critical']),
  message: z.string(),
});

export const alertsResponseSchema = z.object({
  region: z.string(),
  period: z.string(),
  alerts: z.array(alertItemSchema),
});

export const syncRunInfoSchema = z.object({
  id: z.number(),
  created_at: z.string(),
  provider: z.string(),
  total_items: z.number(),
  relevant_items: z.number(),
  quality_passed: z.boolean(),
  reason: z.string(),
});

export const syncRunsResponseSchema = z.object({
  region: z.string(),
  period: z.string(),
  runs: z.array(syncRunInfoSchema),
});

export const snapshotInfoSchema = z.object({
  created_at: z.string(),
  item_count: z.number(),
});

export const snapshotsResponseSchema = z.object({
  region: z.string(),
  period: z.string(),
  snapshots: z.array(snapshotInfoSchema),
});

export const healthResponseSchema = z.object({
  status: z.string(),
});

export const readyResponseSchema = z.object({
  status: z.string(),
  fresh: z.boolean(),
});

export const syncResponseSchema = z.object({
  status: z.string(),
  saved: z.number(),
});
