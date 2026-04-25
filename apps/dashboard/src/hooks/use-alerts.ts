import { useQuery } from '@tanstack/react-query';
import { fetchAlerts } from '@/api/admin';
import type { AlertsResponse } from '@/api/types';

export function useAlerts() {
  return useQuery<AlertsResponse, Error>({
    queryKey: ['admin', 'alerts'],
    queryFn: fetchAlerts,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
