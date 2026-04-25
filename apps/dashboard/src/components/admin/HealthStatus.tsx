import { Activity } from 'lucide-react';
import { useHealthStatus } from '@/hooks/use-health-status';
import GlassCard from '@/components/ui/GlassCard';
import StatusDot from '@/components/ui/StatusDot';
import Skeleton from '@/components/ui/Skeleton';

function HealthRowSkeleton() {
  return (
    <div className="flex items-center gap-3 py-2">
      <Skeleton variant="text" className="w-8 h-3" />
      <Skeleton variant="text" className="w-32 h-3" />
    </div>
  );
}

export default function HealthStatus() {
  const { data, isLoading } = useHealthStatus();

  return (
    <GlassCard>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-gray-400 shrink-0" aria-hidden="true" />
          <h2 className="text-base font-semibold text-gray-100">System Health</h2>
        </div>

        {isLoading || !data ? (
          <div className="flex flex-col gap-2">
            <HealthRowSkeleton />
            <HealthRowSkeleton />
          </div>
        ) : (
          <div className="flex flex-col divide-y divide-white/5">
            <div className="flex items-center gap-3 py-3">
              <span className="w-10 text-xs font-medium text-gray-400">API</span>
              <StatusDot
                status={data.health.status === 'ok' ? 'healthy' : 'critical'}
                pulse={data.health.status !== 'ok'}
              />
              <span className="text-sm text-gray-300">{data.health.status}</span>
            </div>

            <div className="flex items-center gap-3 py-3">
              <span className="w-10 text-xs font-medium text-gray-400">Data</span>
              <StatusDot
                status={data.ready.fresh ? 'healthy' : 'warning'}
                pulse={!data.ready.fresh}
              />
              <span className="text-sm text-gray-300">{data.ready.status}</span>
              <span className="text-xs text-gray-500">
                fresh: {data.ready.fresh ? 'true' : 'false'}
              </span>
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}
