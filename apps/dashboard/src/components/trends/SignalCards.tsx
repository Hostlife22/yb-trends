import { Play, TrendingUp, Search, Activity } from 'lucide-react';
import type { ClassifiedTrendItem } from '@/api/types';
import { formatNumber } from '@/lib/formatters';

interface SignalCardsProps {
  item: ClassifiedTrendItem;
}

interface CardProps {
  label: string;
  value: string;
  hint?: string;
  icon: React.ReactNode;
}

function Card({ label, value, hint, icon }: CardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
          {label}
        </span>
        <span className="text-gray-500">{icon}</span>
      </div>
      <div className="mt-3 text-2xl font-semibold text-white tabular-nums">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
    </div>
  );
}

function pct(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export default function SignalCards({ item }: SignalCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <Card
        label="YT Views (14d)"
        value={item.youtube_total_views_14d ? formatNumber(item.youtube_total_views_14d) : '—'}
        hint={
          item.youtube_videos_published_14d
            ? `${item.youtube_videos_published_14d} videos · ${item.youtube_channels_count_14d} channels`
            : 'No recent videos found'
        }
        icon={<Play className="h-4 w-4" />}
      />
      <Card
        label="YT median views"
        value={item.youtube_median_views_14d ? formatNumber(item.youtube_median_views_14d) : '—'}
        hint={
          item.youtube_top_video_views_14d
            ? `top: ${formatNumber(item.youtube_top_video_views_14d)}`
            : undefined
        }
        icon={<TrendingUp className="h-4 w-4" />}
      />
      <Card
        label="Search demand"
        value={pct(item.search_demand)}
        hint={`momentum ${pct(item.search_momentum)}`}
        icon={<Search className="h-4 w-4" />}
      />
      <Card
        label="YT demand"
        value={pct(item.youtube_demand)}
        hint={`freshness ${pct(item.youtube_freshness)}`}
        icon={<Activity className="h-4 w-4" />}
      />
    </div>
  );
}
