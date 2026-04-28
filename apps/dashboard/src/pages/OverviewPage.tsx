import { memo, useCallback, useMemo, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import AlertsBanner from '@/components/overview/AlertsBanner';
import MetricsGrid from '@/components/overview/MetricsGrid';
import SummaryCard from '@/components/overview/SummaryCard';
import { TrendCard } from '@/components/trends';
import Skeleton from '@/components/ui/Skeleton';
import ErrorBanner from '@/components/ui/ErrorBanner';
import { useTopTrends } from '@/hooks/use-top-trends';
import type { ClassifiedTrendItem } from '@/api/types';

const ScoreDistribution = lazy(() => import('@/components/charts/ScoreDistribution'));
const StudioPieChart = lazy(() => import('@/components/charts/StudioPieChart'));

const SKELETON_KEYS = ['s1', 's2', 's3', 's4', 's5'] as const;

function ChartFallback() {
  return <Skeleton variant="card" className="h-[300px]" />;
}

interface TrendCardItemProps {
  item: ClassifiedTrendItem;
  rank: number;
  onSelect: (query: string) => void;
}

const TrendCardItem = memo(function TrendCardItem({ item, rank, onSelect }: TrendCardItemProps) {
  const handleClick = useCallback(() => onSelect(item.query), [item.query, onSelect]);
  return <TrendCard item={item} rank={rank} onClick={handleClick} />;
});

function TopTrendsGrid({
  items,
  onSelect,
}: {
  items: ClassifiedTrendItem[];
  onSelect: (query: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {items.map((item, idx) => (
        <TrendCardItem
          key={item.query}
          item={item}
          rank={idx + 1}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

export default function OverviewPage() {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useTopTrends({ limit: 20 });

  const items = data?.items;
  const topFive = useMemo(() => items?.slice(0, 5) ?? [], [items]);
  const hasItems = (items?.length ?? 0) > 0;

  const handleSelect = useCallback(
    (query: string) => {
      navigate(`/trends/${encodeURIComponent(query)}`);
    },
    [navigate],
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-100">Overview</h1>
        <p className="mt-1 text-sm text-gray-500">
          Movie & animation trend insights at a glance
        </p>
      </div>

      <AlertsBanner />
      <MetricsGrid />
      <SummaryCard />

      <section>
        <h2 className="mb-4 text-lg font-medium text-gray-200">Top Trends</h2>
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {SKELETON_KEYS.map((k) => (
              <Skeleton key={k} variant="card" />
            ))}
          </div>
        ) : error ? (
          <ErrorBanner message="Failed to load trends" onRetry={refetch} />
        ) : (
          <TopTrendsGrid items={topFive} onSelect={handleSelect} />
        )}
      </section>

      {hasItems && items && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="glass p-6">
            <h2 className="mb-4 text-lg font-medium text-gray-200">Score Distribution</h2>
            <Suspense fallback={<ChartFallback />}>
              <ScoreDistribution items={items} />
            </Suspense>
          </div>
          <div className="glass p-6">
            <h2 className="mb-4 text-lg font-medium text-gray-200">Studios</h2>
            <Suspense fallback={<ChartFallback />}>
              <StudioPieChart items={items} />
            </Suspense>
          </div>
        </div>
      )}
    </div>
  );
}
