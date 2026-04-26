import { useMutation, useQueryClient } from '@tanstack/react-query';
import { triggerSync } from '@/api/admin';
import type { SyncResponse } from '@/api/types';

interface SyncVariables {
  region?: string;
  period?: string;
}

export function useSync() {
  const queryClient = useQueryClient();

  return useMutation<SyncResponse, Error, SyncVariables>({
    mutationFn: ({ region, period }: SyncVariables) => triggerSync(region, period),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin', 'metrics'] });
      void queryClient.invalidateQueries({ queryKey: ['admin', 'sync-runs'] });
      void queryClient.invalidateQueries({ queryKey: ['admin', 'snapshots'] });
      void queryClient.invalidateQueries({ queryKey: ['admin', 'alerts'] });
      void queryClient.invalidateQueries({ queryKey: ['trends', 'top'] });
      void queryClient.invalidateQueries({ queryKey: ['summary'] });
    },
  });
}
