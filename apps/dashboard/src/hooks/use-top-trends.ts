import { useQuery } from '@tanstack/react-query';
import { fetchTopTrends } from '@/api/trends';
import type { TopTrendsResponse } from '@/api/types';

export function useTopTrends(limit?: number) {
  return useQuery<TopTrendsResponse, Error>({
    queryKey: ['trends', 'top', limit],
    queryFn: () => fetchTopTrends(limit),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}
