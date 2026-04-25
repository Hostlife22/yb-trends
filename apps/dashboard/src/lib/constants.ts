import type { ContentType, AlertSeverity } from '@/api/types';

export const CONTENT_TYPE_COLORS: Record<ContentType, string> = {
  movie: 'blue',
  animation: 'purple',
  unknown: 'gray',
} as const;

export const SEVERITY_COLORS: Record<AlertSeverity, string> = {
  warning: 'amber',
  critical: 'red',
} as const;

export const ROUTES = {
  overview: '/',
  trends: '/trends',
  trendDetail: '/trends/:query',
  admin: '/admin',
} as const;

export const POLL_INTERVALS = {
  health: 30_000,
  alerts: 60_000,
  metrics: 60_000,
  topTrends: 120_000,
  summary: 120_000,
  timeseries: 120_000,
  syncRuns: 60_000,
  snapshots: 120_000,
} as const;
