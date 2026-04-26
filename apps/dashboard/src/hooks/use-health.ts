import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '@/api/health';
import type { HealthResponse } from '@/api/types';

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: fetchHealth,
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}
