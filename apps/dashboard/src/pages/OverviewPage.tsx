import { useNavigate } from 'react-router-dom';
import AlertsBanner from '@/components/overview/AlertsBanner';
import MetricsGrid from '@/components/overview/MetricsGrid';
import SummaryCard from '@/components/overview/SummaryCard';
import { TrendCard } from '@/components/trends';
import { ScoreDistribution, StudioPieChart } from '@/components/charts';
import Skeleton from '@/components/ui/Skeleton';
import ErrorBanner from '@/components/ui/ErrorBanner';
import { useTopTrends } from '@/hooks/use-top-trends';

export default function OverviewPage() {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useTopTrends(20);

  const items = data?.items ?? [];
  const topFive = items.slice(0, 5);

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

      <div>
        <h2 className="mb-4 text-lg font-medium text-gray-200">Top Trends</h2>
        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} variant="card" />
            ))}
          </div>
        )}
        {error && <ErrorBanner message="Failed to load trends" onRetry={refetch} />}
        {!isLoading && !error && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {topFive.map((item, idx) => (
              <TrendCard
                key={item.query}
                item={item}
                rank={idx + 1}
                onClick={() => navigate(`/trends/${encodeURIComponent(item.query)}`)}
              />
            ))}
          </div>
        )}
      </div>

      {items.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="glass p-6">
            <h2 className="mb-4 text-lg font-medium text-gray-200">Score Distribution</h2>
            <ScoreDistribution items={items} />
          </div>
          <div className="glass p-6">
            <h2 className="mb-4 text-lg font-medium text-gray-200">Studios</h2>
            <StudioPieChart items={items} />
          </div>
        </div>
      )}
    </div>
  );
}
