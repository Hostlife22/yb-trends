import { useQuery } from '@tanstack/react-query';
import { fetchMetrics } from '@/api/admin';
import type { MetricsResponse } from '@/api/types';

export function useMetrics() {
  return useQuery<MetricsResponse, Error>({
    queryKey: ['admin', 'metrics'],
    queryFn: fetchMetrics,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
