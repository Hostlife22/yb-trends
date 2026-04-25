import { useQuery } from '@tanstack/react-query';
import { fetchSnapshots } from '@/api/admin';
import type { SnapshotsResponse } from '@/api/types';

export function useSnapshots(limit?: number) {
  return useQuery<SnapshotsResponse, Error>({
    queryKey: ['admin', 'snapshots', limit],
    queryFn: () => fetchSnapshots(limit),
    staleTime: 60_000,
  });
}
