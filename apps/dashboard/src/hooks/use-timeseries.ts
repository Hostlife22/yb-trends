import { useQuery } from '@tanstack/react-query';
import { fetchTimeseries } from '@/api/trends';
import type { TrendTimeseriesResponse } from '@/api/types';

export function useTimeseries(query: string) {
  return useQuery<TrendTimeseriesResponse, Error>({
    queryKey: ['trends', 'timeseries', query],
    queryFn: () => fetchTimeseries(query),
    staleTime: 60_000,
    enabled: !!query,
  });
}
