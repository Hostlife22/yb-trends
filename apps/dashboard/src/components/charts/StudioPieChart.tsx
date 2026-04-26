import { memo, useMemo } from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';
import { PieChart as PieChartIcon } from 'lucide-react';
import type { ClassifiedTrendItem } from '@/api/types';
import EmptyState from '@/components/ui/EmptyState';

interface StudioPieChartProps {
  items: ClassifiedTrendItem[];
}

const PIE_HEIGHT = 260;
const INNER_RADIUS = 55;
const OUTER_RADIUS = 95;
const LEGEND_MAX_HEIGHT = 140;

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
      <div style={{ height: PIE_HEIGHT }}>
        <EmptyState icon={PieChartIcon} title="No studio data available" />
      </div>
    );
  }

  if (isAllUnknown(data)) {
    return (
      <div style={{ height: PIE_HEIGHT }}>
        <EmptyState
          icon={PieChartIcon}
          title="No studio data available"
          description="All items have unknown studio"
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div style={{ height: PIE_HEIGHT }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={INNER_RADIUS}
              outerRadius={OUTER_RADIUS}
              dataKey="value"
              paddingAngle={2}
            >
              {data.map((entry, index) => (
                <Cell
                  key={entry.name}
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
          </PieChart>
        </ResponsiveContainer>
      </div>

      <ul
        className="flex flex-wrap gap-x-3 gap-y-1.5 overflow-y-auto pr-1 text-xs text-gray-300"
        style={{ maxHeight: LEGEND_MAX_HEIGHT }}
      >
        {data.map((entry, index) => (
          <li key={entry.name} className="flex min-w-0 items-center gap-1.5">
            <span
              aria-hidden="true"
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: STUDIO_COLORS[index % STUDIO_COLORS.length] }}
            />
            <span className="truncate">
              {entry.name}{' '}
              <span className="text-gray-500">({entry.value})</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default memo(StudioPieChart);
