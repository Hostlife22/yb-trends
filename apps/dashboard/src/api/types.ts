import { z } from 'zod';
import {
  alertItemSchema,
  alertsResponseSchema,
  classifiedTrendItemSchema,
  healthResponseSchema,
  metricsResponseSchema,
  readyResponseSchema,
  snapshotInfoSchema,
  snapshotsResponseSchema,
  summaryResponseSchema,
  syncResponseSchema,
  syncRunInfoSchema,
  syncRunsResponseSchema,
  topTrendsResponseSchema,
  trendPointSchema,
  trendTimeseriesResponseSchema,
} from './schemas';

export type TrendPoint = z.infer<typeof trendPointSchema>;
export type ClassifiedTrendItem = z.infer<typeof classifiedTrendItemSchema>;
export type TopTrendsResponse = z.infer<typeof topTrendsResponseSchema>;
export type SummaryResponse = z.infer<typeof summaryResponseSchema>;
export type TrendTimeseriesResponse = z.infer<typeof trendTimeseriesResponseSchema>;
export type MetricsResponse = z.infer<typeof metricsResponseSchema>;
export type AlertItem = z.infer<typeof alertItemSchema>;
export type AlertsResponse = z.infer<typeof alertsResponseSchema>;
export type SyncRunInfo = z.infer<typeof syncRunInfoSchema>;
export type SyncRunsResponse = z.infer<typeof syncRunsResponseSchema>;
export type SnapshotInfo = z.infer<typeof snapshotInfoSchema>;
export type SnapshotsResponse = z.infer<typeof snapshotsResponseSchema>;
export type HealthResponse = z.infer<typeof healthResponseSchema>;
export type ReadyResponse = z.infer<typeof readyResponseSchema>;
export type SyncResponse = z.infer<typeof syncResponseSchema>;

export type ContentType = ClassifiedTrendItem['content_type'];
export type AlertSeverity = AlertItem['severity'];
