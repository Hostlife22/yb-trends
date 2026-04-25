import { useQueries } from '@tanstack/react-query';
import { fetchHealth, fetchReady } from '@/api/health';
import type { HealthResponse, ReadyResponse } from '@/api/types';

interface HealthStatusData {
  health: HealthResponse;
  ready: ReadyResponse;
}

/**
 * Fetches both /health and /ready in parallel and combines into a single result.
 */
export function useHealthStatus() {
  const [healthQuery, readyQuery] = useQueries({
    queries: [
      {
        queryKey: ['health'],
        queryFn: fetchHealth,
        staleTime: 15_000,
        refetchInterval: 30_000,
      },
      {
        queryKey: ['ready'],
        queryFn: fetchReady,
        staleTime: 15_000,
        refetchInterval: 30_000,
      },
    ],
  });

  const isLoading = healthQuery.isLoading || readyQuery.isLoading;
  const error = healthQuery.error ?? readyQuery.error ?? null;

  const data: HealthStatusData | undefined =
    healthQuery.data && readyQuery.data
      ? { health: healthQuery.data, ready: readyQuery.data }
      : undefined;

  return { data, isLoading, error };
}
