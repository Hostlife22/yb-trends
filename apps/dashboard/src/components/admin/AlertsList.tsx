import { AlertOctagon, AlertTriangle, Bell, CheckCircle } from 'lucide-react';
import clsx from 'clsx';
import { useAlerts } from '@/hooks/use-alerts';
import type { AlertItem } from '@/api/types';
import GlassCard from '@/components/ui/GlassCard';
import Badge from '@/components/ui/Badge';
import EmptyState from '@/components/ui/EmptyState';

const SEVERITY_ORDER: Record<AlertItem['severity'], number> = {
  critical: 0,
  warning: 1,
};

function sortBySeverity(alerts: AlertItem[]): AlertItem[] {
  return [...alerts].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
  );
}

function AlertCard({ alert }: { alert: AlertItem }) {
  const isCritical = alert.severity === 'critical';

  return (
    <div
      className={clsx(
        'flex items-start gap-3 rounded-xl bg-white/5 p-4 border',
        isCritical
          ? 'border-l-4 border-l-red-500 border-red-500/10'
          : 'border-l-4 border-l-amber-500 border-amber-500/10',
      )}
    >
      {isCritical ? (
        <AlertOctagon
          size={16}
          className="mt-0.5 shrink-0 text-red-400"
          aria-hidden="true"
        />
      ) : (
        <AlertTriangle
          size={16}
          className="mt-0.5 shrink-0 text-amber-400"
          aria-hidden="true"
        />
      )}

      <div className="flex flex-1 flex-col gap-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={isCritical ? 'critical' : 'warning'}>{alert.severity}</Badge>
          <code className="text-xs font-mono text-gray-400">{alert.code}</code>
        </div>
        <p className="text-sm text-gray-200">{alert.message}</p>
      </div>
    </div>
  );
}

export default function AlertsList() {
  const { data } = useAlerts();

  const sortedAlerts = data ? sortBySeverity(data.alerts) : [];

  return (
    <GlassCard>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Bell size={18} className="text-gray-400 shrink-0" aria-hidden="true" />
          <h2 className="text-base font-semibold text-gray-100">Alerts</h2>
        </div>

        {sortedAlerts.length === 0 ? (
          <EmptyState
            icon={CheckCircle}
            title="No active alerts"
          />
        ) : (
          <div className="flex flex-col gap-3">
            {sortedAlerts.map((alert) => (
              <AlertCard key={alert.code} alert={alert} />
            ))}
          </div>
        )}
      </div>
    </GlassCard>
  );
}
