import { useMemo, useCallback, useState } from 'react';
import { TrendsTable, TrendFilters } from '@/components/trends';
import type { FilterValues } from '@/components/trends';
import Skeleton from '@/components/ui/Skeleton';
import ErrorBanner from '@/components/ui/ErrorBanner';
import EmptyState from '@/components/ui/EmptyState';
import { useTopTrends } from '@/hooks/use-top-trends';
import { Search } from 'lucide-react';

const DEFAULT_FILTERS: FilterValues = {
  contentType: 'all',
  studio: '',
  minScore: 0,
};

export default function TrendsPage() {
  const { data, isLoading, error, refetch } = useTopTrends(100);
  const [filters, setFilters] = useState<FilterValues>(DEFAULT_FILTERS);

  const items = data?.items ?? [];

  const filtered = useMemo(() => {
    return items.filter((item) => {
      if (filters.contentType !== 'all' && item.content_type !== filters.contentType) {
        return false;
      }
      if (filters.studio && !item.studio.toLowerCase().includes(filters.studio.toLowerCase())) {
        return false;
      }
      if (item.final_score < filters.minScore) {
        return false;
      }
      return true;
    });
  }, [items, filters]);

  const handleFilterChange = useCallback((newFilters: FilterValues) => {
    setFilters(newFilters);
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-100">Trends</h1>
        <p className="mt-1 text-sm text-gray-500">
          All tracked movie & animation trends
        </p>
      </div>

      <TrendFilters
        onFilterChange={handleFilterChange}
        totalCount={items.length}
        filteredCount={filtered.length}
      />

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} variant="row" />
          ))}
        </div>
      )}

      {error && <ErrorBanner message="Failed to load trends" onRetry={refetch} />}

      {!isLoading && !error && filtered.length === 0 && (
        <EmptyState icon={Search} title="No trends found" description="Try adjusting your filters" />
      )}

      {!isLoading && !error && filtered.length > 0 && (
        <TrendsTable items={filtered} />
      )}
    </div>
  );
}
