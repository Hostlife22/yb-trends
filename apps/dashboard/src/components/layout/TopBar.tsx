import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import StatusDot from '../ui/StatusDot';
import MobileNav from './MobileNav';

type HealthStatus = 'healthy' | 'warning' | 'critical';

const ROUTE_TITLES: Record<string, string> = {
  '/': 'Overview',
  '/trends': 'Trends',
  '/admin': 'Admin',
};

function resolveTitle(pathname: string): string {
  return ROUTE_TITLES[pathname] ?? 'Dashboard';
}

function useHealthStatus() {
  const [status, setStatus] = useState<HealthStatus>('healthy');

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      try {
        const res = await fetch('/health', { signal: AbortSignal.timeout(4000) });
        if (cancelled) return;
        setStatus(res.ok ? 'healthy' : 'warning');
      } catch {
        if (!cancelled) setStatus('critical');
      }
    };

    void check();
    const id = setInterval(() => void check(), 30_000);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return status;
}

export default function TopBar() {
  const { pathname } = useLocation();
  const title = resolveTitle(pathname);
  const healthStatus = useHealthStatus();

  const statusLabel: Record<HealthStatus, string> = {
    healthy: 'All systems operational',
    warning: 'Degraded performance',
    critical: 'Service unavailable',
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-white/10 bg-slate-950/80 px-4 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <MobileNav />
        <h1 className="text-base font-semibold text-white">{title}</h1>
      </div>

      <div className="flex items-center gap-2">
        <StatusDot status={healthStatus} pulse={healthStatus !== 'healthy'} />
        <span className="hidden text-xs text-gray-400 sm:inline">
          {statusLabel[healthStatus]}
        </span>
      </div>
    </header>
  );
}
