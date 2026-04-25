import { History } from 'lucide-react';
import { useSyncRuns } from '@/hooks/use-sync-runs';
import GlassCard from '@/components/ui/GlassCard';
import Badge from '@/components/ui/Badge';
import Skeleton from '@/components/ui/Skeleton';
import EmptyState from '@/components/ui/EmptyState';
import { formatDate, formatNumber } from '@/lib/formatters';

const SYNC_RUNS_LIMIT = 50;

function TableSkeletonRows() {
  return (
    <>
      {[0, 1, 2, 3, 4].map((i) => (
        <tr key={i}>
          {[0, 1, 2, 3, 4, 5].map((j) => (
            <td key={j} className="px-4 py-3">
              <Skeleton variant="text" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

export default function SyncRunsTable() {
  const { data, isLoading } = useSyncRuns(SYNC_RUNS_LIMIT);

  const runs = data?.runs ?? [];

  return (
    <GlassCard>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <History size={18} className="text-gray-400 shrink-0" aria-hidden="true" />
          <h2 className="text-base font-semibold text-gray-100">Sync History</h2>
        </div>

        {!isLoading && runs.length === 0 ? (
          <EmptyState title="No sync runs yet" />
        ) : (
          <div className="overflow-x-auto -mx-6">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-left">
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Time
                  </th>
                  <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Provider
                  </th>
                  <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Total
                  </th>
                  <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Relevant
                  </th>
                  <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Quality
                  </th>
                  <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {isLoading ? (
                  <TableSkeletonRows />
                ) : (
                  runs.map((run, idx) => (
                    <tr
                      key={`${run.created_at}-${idx}`}
                      className="transition-colors hover:bg-white/5"
                    >
                      <td className="whitespace-nowrap px-6 py-3 text-gray-300">
                        {formatDate(run.created_at)}
                      </td>
                      <td className="px-4 py-3 text-gray-300">{run.provider}</td>
                      <td className="px-4 py-3 text-gray-300">
                        {formatNumber(run.total_items)}
                      </td>
                      <td className="px-4 py-3 text-gray-300">
                        {formatNumber(run.relevant_items)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={run.quality_passed ? 'success' : 'critical'}>
                          {run.quality_passed ? 'Passed' : 'Failed'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs max-w-xs truncate">
                        {run.reason}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </GlassCard>
  );
}
