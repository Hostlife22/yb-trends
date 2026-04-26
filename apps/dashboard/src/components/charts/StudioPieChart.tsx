import { memo, useMemo } from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import { PieChart as PieChartIcon } from 'lucide-react';
import type { ClassifiedTrendItem } from '@/api/types';
import EmptyState from '@/components/ui/EmptyState';

interface StudioPieChartProps {
  items: ClassifiedTrendItem[];
}

const CHART_HEIGHT = 300;
const INNER_RADIUS = 60;
const OUTER_RADIUS = 100;

const STUDIO_COLORS = [
  '#818cf8',
  '#c084fc',
  '#60a5fa',
  '#34d399',
  '#fbbf24',
  '#fb7185',
  '#22d3ee',
  '#a78bfa',
  '#4ade80',
  '#f472b6',
] as const;

const tooltipStyle = {
  backgroundColor: '#111827',
  border: '1px solid #374151',
  borderRadius: '8px',
  color: '#f9fafb',
  fontSize: '12px',
} as const;

interface StudioEntry {
  name: string;
  value: number;
}

function groupByStudio(items: ClassifiedTrendItem[]): StudioEntry[] {
  const counts = items.reduce<Record<string, number>>((acc, item) => {
    const studio = item.studio || 'Unknown';
    return { ...acc, [studio]: (acc[studio] ?? 0) + 1 };
  }, {});

  return Object.entries(counts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
}

function isAllUnknown(entries: StudioEntry[]): boolean {
  return entries.every(
    (e) => e.name.toLowerCase() === 'unknown' || e.name === '',
  );
}

function StudioPieChart({ items }: StudioPieChartProps) {
  const data = useMemo(() => groupByStudio(items), [items]);

  if (items.length === 0) {
    return (
      <div style={{ height: CHART_HEIGHT }}>
        <EmptyState icon={PieChartIcon} title="No studio data available" />
      </div>
    );
  }

  if (isAllUnknown(data)) {
    return (
      <div style={{ height: CHART_HEIGHT }}>
        <EmptyState
          icon={PieChartIcon}
          title="No studio data available"
          description="All items have unknown studio"
        />
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={INNER_RADIUS}
          outerRadius={OUTER_RADIUS}
          dataKey="value"
          paddingAngle={2}
        >
          {data.map((_, index) => (
            <Cell
              key={index}
              fill={STUDIO_COLORS[index % STUDIO_COLORS.length]}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={tooltipStyle}
          itemStyle={{ color: '#f9fafb' }}
          labelStyle={{ color: '#f9fafb', fontWeight: 600 }}
          formatter={(value: number, name: string) => [value, name]}
        />
        <Legend
          wrapperStyle={{ color: '#9ca3af', fontSize: '12px' }}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export default memo(StudioPieChart);
