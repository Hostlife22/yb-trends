import { TrendingUp, TrendingDown } from 'lucide-react';
import clsx from 'clsx';
import type { ClassifiedTrendItem } from '@/api/types';
import Badge from '@/components/ui/Badge';
import ScoreBar from '@/components/ui/ScoreBar';
import { formatNumber, formatScore } from '@/lib/formatters';

interface TrendRowProps {
  item: ClassifiedTrendItem;
  rank: number;
  onClick?: () => void;
}

const GROWTH_THRESHOLD = 0;

export default function TrendRow({ item, rank, onClick }: TrendRowProps) {
  const isPositiveGrowth = item.growth_velocity > GROWTH_THRESHOLD;
  const confidencePercent = Math.round(item.confidence * 100);

  return (
    <tr
      className={clsx(
        'border-b border-white/5 transition-colors duration-150',
        onClick && 'cursor-pointer hover:bg-white/5',
      )}
      onClick={onClick}
    >
      <td className="py-3 pl-4 pr-3 text-sm font-medium text-gray-500 w-10">
        {rank}
      </td>
      <td className="py-3 px-3 text-sm font-medium text-white max-w-[200px]">
        <span className="truncate block">{item.title_normalized}</span>
      </td>
      <td className="py-3 px-3 whitespace-nowrap">
        <Badge variant={item.content_type}>{item.content_type}</Badge>
      </td>
      <td className="py-3 px-3 text-sm text-gray-400 whitespace-nowrap">
        {item.release_year ?? '—'}
      </td>
      <td className="py-3 px-3 text-sm text-gray-400 whitespace-nowrap uppercase">
        {item.original_language ?? '—'}
      </td>
      <td className="py-3 px-3 text-sm text-gray-400 whitespace-nowrap">
        {item.studio || '—'}
      </td>
      <td className="py-3 px-3 w-32">
        <div className="flex items-center gap-2">
          <ScoreBar score={item.final_score} className="flex-1" />
          <span className="text-xs text-gray-400 w-8 text-right shrink-0">
            {formatScore(item.final_score)}
          </span>
        </div>
      </td>
      <td className="py-3 px-3 text-sm text-gray-300 whitespace-nowrap text-right">
        {item.youtube_total_views_14d
          ? formatNumber(item.youtube_total_views_14d)
          : '—'}
      </td>
      <td className="py-3 px-3 text-sm text-gray-300 whitespace-nowrap text-right">
        {item.youtube_videos_published_14d || '—'}
      </td>
      <td className="py-3 px-3 text-sm text-gray-300 whitespace-nowrap text-right">
        {formatNumber(item.interest_level)}
      </td>
      <td className="py-3 px-3 whitespace-nowrap">
        <div className="flex items-center gap-1">
          {isPositiveGrowth ? (
            <TrendingUp size={13} className="text-emerald-400 shrink-0" />
          ) : (
            <TrendingDown size={13} className="text-red-400 shrink-0" />
          )}
          <span
            className={clsx(
              'text-sm font-medium',
              isPositiveGrowth ? 'text-emerald-400' : 'text-red-400',
            )}
          >
            {isPositiveGrowth ? '+' : ''}
            {formatScore(item.growth_velocity)}
          </span>
        </div>
      </td>
      <td className="py-3 pr-4 pl-3 text-sm text-gray-400 text-right whitespace-nowrap">
        {confidencePercent}%
      </td>
    </tr>
  );
}
