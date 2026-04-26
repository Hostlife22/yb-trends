import { AlertTriangle, CheckCircle, Clock, RefreshCw, XCircle } from 'lucide-react';
import { useMetrics } from '@/hooks/use-metrics';
import GlassCard from '@/components/ui/GlassCard';
import Skeleton from '@/components/ui/Skeleton';
import StatusDot from '@/components/ui/StatusDot';
import { formatDuration, formatNumber } from '@/lib/formatters';
import {
  SNAPSHOT_AGE_HEALTHY_SECONDS,
  SNAPSHOT_AGE_WARNING_SECONDS,
} from '@/lib/constants';

function resolveSnapshotAgeStatus(
  ageSeconds: number | null,
): 'healthy' | 'warning' | 'critical' {
  if (ageSeconds === null) return 'critical';
  if (ageSeconds < SNAPSHOT_AGE_HEALTHY_SECONDS) return 'healthy';
  if (ageSeconds < SNAPSHOT_AGE_WARNING_SECONDS) return 'warning';
  return 'critical';
}

function MetricCardSkeleton() {
  return (
    <GlassCard>
      <div className="flex flex-col gap-3">
        <Skeleton variant="text" className="w-24" />
        <Skeleton variant="text" className="w-16 h-8" />
        <Skeleton variant="text" className="w-20" />
      </div>
    </GlassCard>
  );
}

export default function MetricsGrid() {
  const { data, isLoading } = useMetrics();

  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  const snapshotAgeStatus = resolveSnapshotAgeStatus(data.latest_snapshot_age_seconds);
  const qualityStatus = data.latest_sync_quality_passed === true ? 'healthy' : 'critical';
  const qualityLabel = data.latest_sync_quality_passed === true ? 'Passed' : 'Failed';
  const hasFailures = data.quality_failures_last_24h > 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {/* Snapshot Age */}
      <GlassCard>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-gray-400">
            <Clock size={16} aria-hidden="true" />
            <span className="text-xs font-medium uppercase tracking-wide">
              Snapshot Age
            </span>
          </div>
          <div className="flex items-center gap-2">
            <StatusDot status={snapshotAgeStatus} pulse={snapshotAgeStatus !== 'healthy'} />
            <span className="text-2xl font-semibold text-gray-100">
              {data.latest_snapshot_age_seconds !== null
                ? formatDuration(data.latest_snapshot_age_seconds)
                : 'N/A'}
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Sync Runs */}
      <GlassCard>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-gray-400">
            <RefreshCw size={16} aria-hidden="true" />
            <span className="text-xs font-medium uppercase tracking-wide">
              Syncs (24h)
            </span>
          </div>
          <span className="text-2xl font-semibold text-gray-100">
            {formatNumber(data.sync_runs_last_24h)}
          </span>
        </div>
      </GlassCard>

      {/* Quality Gate */}
      <GlassCard>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-gray-400">
            {data.latest_sync_quality_passed === true ? (
              <CheckCircle size={16} aria-hidden="true" />
            ) : (
              <XCircle size={16} aria-hidden="true" />
            )}
            <span className="text-xs font-medium uppercase tracking-wide">
              Quality Gate
            </span>
          </div>
          <div className="flex items-center gap-2">
            <StatusDot status={qualityStatus} pulse={qualityStatus === 'critical'} />
            <span className="text-2xl font-semibold text-gray-100">
              {qualityLabel}
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Failures */}
      <GlassCard>
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-gray-400">
            <AlertTriangle size={16} aria-hidden="true" />
            <span className="text-xs font-medium uppercase tracking-wide">
              Failures (24h)
            </span>
          </div>
          <span
            className={
              hasFailures ? 'text-2xl font-semibold text-red-400' : 'text-2xl font-semibold text-gray-100'
            }
          >
            {formatNumber(data.quality_failures_last_24h)}
          </span>
        </div>
      </GlassCard>
    </div>
  );
}
