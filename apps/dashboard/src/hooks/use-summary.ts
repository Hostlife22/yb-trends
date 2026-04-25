import { useQuery } from '@tanstack/react-query';
import { fetchSummary } from '@/api/trends';
import type { SummaryResponse } from '@/api/types';

export function useSummary() {
  return useQuery<SummaryResponse, Error>({
    queryKey: ['summary'],
    queryFn: () => fetchSummary(),
    staleTime: 120_000,
  });
}
