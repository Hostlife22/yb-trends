import { useQuery } from '@tanstack/react-query';
import { fetchSyncRuns } from '@/api/admin';
import type { SyncRunsResponse } from '@/api/types';

export function useSyncRuns(limit?: number) {
  return useQuery<SyncRunsResponse, Error>({
    queryKey: ['admin', 'sync-runs', limit],
    queryFn: () => fetchSyncRuns(limit),
    staleTime: 30_000,
  });
}
