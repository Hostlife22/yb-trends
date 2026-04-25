import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { BarChart2 } from 'lucide-react';
import type { ClassifiedTrendItem } from '@/api/types';
import EmptyState from '@/components/ui/EmptyState';

interface ScoreDistributionProps {
  items: ClassifiedTrendItem[];
}

const MAX_ITEMS = 10;
const TRUNCATE_LENGTH = 20;
const CHART_HEIGHT = 350;
const GRADIENT_ID = 'scoreBarGradient';

function truncate(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength)}\u2026` : text;
}

const tooltipStyle = {
  backgroundColor: '#111827',
  border: '1px solid #374151',
  borderRadius: '8px',
  color: '#f9fafb',
  fontSize: '12px',
} as const;

export default function ScoreDistribution({ items }: ScoreDistributionProps) {
  if (items.length === 0) {
    return (
      <div style={{ height: CHART_HEIGHT }}>
        <EmptyState icon={BarChart2} title="No score data available" />
      </div>
    );
  }

  const topItems = [...items]
    .sort((a, b) => b.final_score - a.final_score)
    .slice(0, MAX_ITEMS)
    .map((item) => ({
      name: truncate(item.title_normalized, TRUNCATE_LENGTH),
      score: item.final_score,
    }));

  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <BarChart
        layout="vertical"
        data={topItems}
        margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
      >
        <defs>
          <linearGradient id={GRADIENT_ID} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
        <XAxis
          type="number"
          tick={{ fill: '#9ca3af', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={140}
          tick={{ fill: '#9ca3af', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ fill: 'rgba(255,255,255,0.04)' }}
          formatter={(value: number) => [value.toFixed(1), 'Score']}
        />
        <Bar dataKey="score" radius={[0, 4, 4, 0]}>
          {topItems.map((_, index) => (
            <Cell key={index} fill={`url(#${GRADIENT_ID})`} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
