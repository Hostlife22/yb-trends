import { Sparkles } from 'lucide-react';
import { useSummary } from '@/hooks/use-summary';
import GlassCard from '@/components/ui/GlassCard';
import Skeleton from '@/components/ui/Skeleton';
import ErrorBanner from '@/components/ui/ErrorBanner';
import { formatDate } from '@/lib/formatters';

function SummaryCardSkeleton() {
  return (
    <GlassCard className="p-8">
      <div className="flex flex-col gap-4">
        <Skeleton variant="text" className="w-32" />
        <Skeleton variant="text" />
        <Skeleton variant="text" />
        <Skeleton variant="text" className="w-3/4" />
      </div>
    </GlassCard>
  );
}

export default function SummaryCard() {
  const { data, isLoading, error } = useSummary();

  if (isLoading) {
    return <SummaryCardSkeleton />;
  }

  if (error || !data) {
    return (
      <GlassCard className="p-8">
        <ErrorBanner message={error?.message ?? 'Failed to load summary'} />
      </GlassCard>
    );
  }

  return (
    <GlassCard className="p-8">
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-2">
          <Sparkles
            size={18}
            className="shrink-0 text-indigo-400"
            aria-hidden="true"
          />
          <span className="text-sm font-semibold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            AI Summary
          </span>
        </div>

        <p className="text-lg leading-relaxed text-gray-200">{data.summary}</p>

        {data.top_titles.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {data.top_titles.map((title) => (
              <span
                key={title}
                className="inline-flex items-center rounded-full bg-white/5 border border-white/10 px-3 py-1 text-xs font-medium text-gray-300 backdrop-blur-xl"
              >
                {title}
              </span>
            ))}
          </div>
        )}

        <p className="text-xs text-gray-500">
          Updated {formatDate(data.generated_at)}
        </p>
      </div>
    </GlassCard>
  );
}
