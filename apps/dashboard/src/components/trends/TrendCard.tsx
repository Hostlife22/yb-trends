import { memo } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import clsx from 'clsx';
import type { ClassifiedTrendItem } from '@/api/types';
import GlassCard from '@/components/ui/GlassCard';
import Badge from '@/components/ui/Badge';
import ScoreBar from '@/components/ui/ScoreBar';
import { formatNumber, formatScore } from '@/lib/formatters';

interface TrendCardProps {
  item: ClassifiedTrendItem;
  rank: number;
  onClick?: () => void;
}

const GROWTH_THRESHOLD = 0;

function TrendCard({ item, rank, onClick }: TrendCardProps) {
  const isPositiveGrowth = item.growth_velocity > GROWTH_THRESHOLD;

  return (
    <GlassCard
      className={clsx(
        'transition-colors duration-200',
        onClick && 'cursor-pointer hover:bg-white/10',
      )}
      onClick={onClick}
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-start gap-3">
          <span className="text-3xl font-bold text-gray-600 leading-none select-none">
            {rank}
          </span>
          <h3 className="text-base font-semibold text-white leading-tight flex-1 min-w-0">
            {item.title_normalized}
          </h3>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={item.content_type}>{item.content_type}</Badge>
          {item.studio && (
            <span className="text-xs text-gray-400 truncate">
              {item.studio}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Score</span>
            <span className="text-xs font-medium text-gray-300">
              {formatScore(item.final_score)}
            </span>
          </div>
          <ScoreBar score={item.final_score} />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            {isPositiveGrowth ? (
              <TrendingUp size={14} className="text-emerald-400" />
            ) : (
              <TrendingDown size={14} className="text-red-400" />
            )}
            <span
              className={clsx(
                'text-xs font-medium',
                isPositiveGrowth ? 'text-emerald-400' : 'text-red-400',
              )}
            >
              {isPositiveGrowth ? '+' : ''}
              {formatScore(item.growth_velocity)}
            </span>
          </div>
          <span className="text-xs text-gray-500">
            Interest:{' '}
            <span className="text-gray-300 font-medium">
              {formatNumber(item.interest_level)}
            </span>
          </span>
        </div>
      </div>
    </GlassCard>
  );
}

export default memo(TrendCard);
