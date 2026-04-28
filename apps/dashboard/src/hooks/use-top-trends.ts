import { useQuery } from '@tanstack/react-query';
import { fetchTopTrends, type TopTrendsFilters } from '@/api/trends';
import type { TopTrendsResponse } from '@/api/types';

export function useTopTrends(filters: TopTrendsFilters = {}) {
  return useQuery<TopTrendsResponse, Error>({
    queryKey: [
      'trends',
      'top',
      filters.limit,
      filters.language ?? null,
      filters.country ?? null,
      filters.minYear ?? null,
      filters.maxYear ?? null,
      filters.sortBy ?? 'final_score',
    ],
    queryFn: () => fetchTopTrends(filters),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}
