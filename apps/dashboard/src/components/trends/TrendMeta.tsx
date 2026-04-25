import clsx from 'clsx';
import type { ClassifiedTrendItem } from '@/api/types';
import GlassCard from '@/components/ui/GlassCard';
import Badge from '@/components/ui/Badge';
import ScoreBar from '@/components/ui/ScoreBar';
import { formatNumber, formatScore } from '@/lib/formatters';

interface TrendMetaProps {
  item: ClassifiedTrendItem;
}

interface MetaRowProps {
  label: string;
  children: React.ReactNode;
}

function MetaRow({ label, children }: MetaRowProps) {
  return (
    <div className="flex items-start justify-between gap-4 py-2.5 border-b border-white/5 last:border-0">
      <span className="text-sm text-gray-400 shrink-0 w-40">{label}</span>
      <div className="flex-1 min-w-0 text-right">{children}</div>
    </div>
  );
}

const GROWTH_THRESHOLD = 0;

export default function TrendMeta({ item }: TrendMetaProps) {
  const isPositiveGrowth = item.growth_velocity > GROWTH_THRESHOLD;
  const confidencePercent = Math.round(item.confidence * 100);

  return (
    <GlassCard>
      <div className="flex flex-col">
        <MetaRow label="Query">
          <span className="text-sm font-mono text-gray-300">{item.query}</span>
        </MetaRow>

        <MetaRow label="Normalized Title">
          <span className="text-sm font-medium text-white">
            {item.title_normalized}
          </span>
        </MetaRow>

        <MetaRow label="Content Type">
          <Badge variant={item.content_type}>{item.content_type}</Badge>
        </MetaRow>

        <MetaRow label="Studio">
          <span className="text-sm text-gray-300">{item.studio || '—'}</span>
        </MetaRow>

        <MetaRow label="Confidence">
          <div className="flex flex-col items-end gap-1.5">
            <span className="text-sm font-medium text-gray-300">
              {confidencePercent}%
            </span>
            <div className="w-32">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                  style={{ width: `${confidencePercent}%` }}
                />
              </div>
            </div>
          </div>
        </MetaRow>

        <MetaRow label="Interest Level">
          <span className="text-sm font-medium text-gray-300">
            {formatNumber(item.interest_level)}
          </span>
        </MetaRow>

        <MetaRow label="Growth Velocity">
          <span
            className={clsx(
              'text-sm font-medium',
              isPositiveGrowth ? 'text-emerald-400' : 'text-red-400',
            )}
          >
            {isPositiveGrowth ? '+' : ''}
            {formatScore(item.growth_velocity)}
          </span>
        </MetaRow>

        <MetaRow label="Final Score">
          <div className="flex flex-col items-end gap-1.5">
            <span className="text-sm font-medium text-gray-300">
              {formatScore(item.final_score)}
            </span>
            <div className="w-32">
              <ScoreBar score={item.final_score} />
            </div>
          </div>
        </MetaRow>

        <MetaRow label="Classification Reason">
          <p className="text-sm text-gray-400 leading-relaxed text-left">
            {item.reason}
          </p>
        </MetaRow>
      </div>
    </GlassCard>
  );
}
