import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { TimeseriesChart } from '@/components/charts';
import { TrendMeta } from '@/components/trends';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Skeleton from '@/components/ui/Skeleton';
import ErrorBanner from '@/components/ui/ErrorBanner';
import EmptyState from '@/components/ui/EmptyState';
import { useTimeseries } from '@/hooks/use-timeseries';
import { useTopTrends } from '@/hooks/use-top-trends';

export default function TrendDetailPage() {
  const { query: rawQuery } = useParams<{ query: string }>();
  const navigate = useNavigate();
  const query = rawQuery ? decodeURIComponent(rawQuery) : '';

  const { data: timeseriesData, isLoading: tsLoading, error: tsError, refetch: tsRefetch } = useTimeseries(query);
  const { data: trendsData } = useTopTrends(100);

  const item = trendsData?.items.find(
    (i) => i.query === query || i.title_normalized === query
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <Button variant="secondary" size="sm" onClick={() => navigate('/trends')}>
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-semibold text-gray-100">
            {item?.title_normalized ?? query}
          </h1>
          <div className="mt-1 flex items-center gap-2">
            {item && (
              <>
                <Badge variant={item.content_type === 'movie' ? 'movie' : item.content_type === 'animation' ? 'animation' : 'unknown'}>
                  {item.content_type}
                </Badge>
                {item.studio !== 'unknown' && (
                  <span className="text-sm text-gray-400">{item.studio}</span>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {item && <TrendMeta item={item} />}

      {!item && !tsLoading && (
        <EmptyState title="Trend not found" description={`No data available for "${query}"`} />
      )}

      <div className="glass p-6">
        <h2 className="mb-4 text-lg font-medium text-gray-200">Interest Over Time</h2>
        {tsLoading && <Skeleton variant="card" className="h-[300px]" />}
        {tsError && <ErrorBanner message="Failed to load timeseries" onRetry={tsRefetch} />}
        {!tsLoading && !tsError && (
          <TimeseriesChart points={timeseriesData?.points ?? []} />
        )}
      </div>
    </div>
  );
}
