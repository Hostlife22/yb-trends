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
      void queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });
}
