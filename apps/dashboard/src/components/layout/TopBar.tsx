import { useLocation } from 'react-router-dom';
import StatusDot from '../ui/StatusDot';
import { useHealth } from '@/hooks/use-health';

type HealthStatus = 'healthy' | 'warning' | 'critical';

const ROUTE_TITLES: Record<string, string> = {
  '/': 'Overview',
  '/trends': 'Trends',
  '/admin': 'Admin',
};

const STATUS_LABELS: Record<HealthStatus, string> = {
  healthy: 'All systems operational',
  warning: 'Degraded performance',
  critical: 'Service unavailable',
};

function resolveTitle(pathname: string): string {
  return ROUTE_TITLES[pathname] ?? 'Dashboard';
}

function deriveStatus(isError: boolean, status: string | undefined): HealthStatus {
  if (isError) return 'critical';
  if (status === 'ok') return 'healthy';
  return 'warning';
}

export default function TopBar() {
  const { pathname } = useLocation();
  const title = resolveTitle(pathname);
  const { data, isError } = useHealth();
  const healthStatus = deriveStatus(isError, data?.status);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-white/10 bg-slate-950/80 px-4 pl-16 backdrop-blur-xl md:pl-4">
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold text-white">{title}</h1>
      </div>

      <div className="flex items-center gap-2">
        <StatusDot status={healthStatus} pulse={healthStatus !== 'healthy'} />
        <span className="hidden text-xs text-gray-400 sm:inline">
          {STATUS_LABELS[healthStatus]}
        </span>
      </div>
    </header>
  );
}
