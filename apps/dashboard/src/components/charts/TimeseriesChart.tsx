import { useEffect, useRef } from 'react';
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type AreaSeriesOptions,
  type Time,
} from 'lightweight-charts';
import { Activity } from 'lucide-react';
import type { TrendPoint } from '@/api/types';
import EmptyState from '@/components/ui/EmptyState';

interface TimeseriesChartProps {
  points: TrendPoint[];
  title?: string;
  height?: number;
}

const CHART_COLORS = {
  lineColor: '#6366f1',
  areaTopColor: 'rgba(99, 102, 241, 0.4)',
  areaBottomColor: 'rgba(99, 102, 241, 0.02)',
  textColor: '#9ca3af',
  gridColor: '#1f2937',
} as const;

export default function TimeseriesChart({
  points,
  title,
  height = 300,
}: TimeseriesChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      height,
      layout: {
        background: { color: 'transparent' },
        textColor: CHART_COLORS.textColor,
      },
      grid: {
        vertLines: { color: CHART_COLORS.gridColor },
        horzLines: { color: CHART_COLORS.gridColor },
      },
      crosshair: {
        vertLine: { color: '#4b5563', width: 1 },
        horzLine: { color: '#4b5563', width: 1 },
      },
      rightPriceScale: {
        borderColor: '#374151',
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: true,
      },
    });

    const areaSeriesOptions: Partial<AreaSeriesOptions> = {
      lineColor: CHART_COLORS.lineColor,
      topColor: CHART_COLORS.areaTopColor,
      bottomColor: CHART_COLORS.areaBottomColor,
      lineWidth: 2,
    };

    const series = chart.addAreaSeries(areaSeriesOptions);

    chartRef.current = chart;
    seriesRef.current = series;

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry && chartRef.current) {
        chartRef.current.applyOptions({ width: entry.contentRect.width });
      }
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chartRef.current?.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || !chartRef.current) return;

    const data = points
      .map((point) => ({
        time: point.timestamp.slice(0, 10) as Time,
        value: point.interest,
      }))
      .sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));

    seriesRef.current.setData(data);

    if (data.length > 0) {
      chartRef.current.timeScale().fitContent();
    }
  }, [points]);

  if (points.length === 0) {
    return (
      <div style={{ height }}>
        <EmptyState icon={Activity} title="No timeseries data" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {title && (
        <h3 className="text-sm font-medium text-gray-300">{title}</h3>
      )}
      <div ref={containerRef} style={{ height }} />
    </div>
  );
}
