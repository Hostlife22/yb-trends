import { useState } from 'react';
import { AlertOctagon, AlertTriangle, X } from 'lucide-react';
import clsx from 'clsx';
import { useAlerts } from '@/hooks/use-alerts';
import type { AlertItem } from '@/api/types';

function AlertRow({
  alert,
  onDismiss,
}: {
  alert: AlertItem;
  onDismiss: (code: string) => void;
}) {
  const isCritical = alert.severity === 'critical';

  return (
    <div
      className={clsx(
        'flex items-start gap-3 rounded-2xl border bg-white/5 p-4 backdrop-blur-xl',
        isCritical
          ? 'border-l-4 border-l-red-500 border-red-500/20'
          : 'border-l-4 border-l-amber-500 border-amber-500/20',
      )}
    >
      {isCritical ? (
        <AlertOctagon
          size={18}
          className="mt-0.5 shrink-0 text-red-400"
          aria-hidden="true"
        />
      ) : (
        <AlertTriangle
          size={18}
          className="mt-0.5 shrink-0 text-amber-400"
          aria-hidden="true"
        />
      )}

      <div className="flex flex-1 items-start gap-2 min-w-0">
        <span
          className={clsx(
            'inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
            isCritical
              ? 'bg-red-500/20 text-red-400'
              : 'bg-amber-500/20 text-amber-400',
          )}
        >
          {alert.severity}
        </span>
        <p className="text-sm text-gray-200">{alert.message}</p>
      </div>

      <button
        type="button"
        onClick={() => onDismiss(alert.code)}
        aria-label={`Dismiss alert ${alert.code}`}
        className="shrink-0 rounded-lg p-1 text-gray-500 transition-colors hover:bg-white/10 hover:text-gray-300"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export default function AlertsBanner() {
  const { data } = useAlerts();
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const handleDismiss = (code: string) => {
    setDismissed((prev) => new Set([...prev, code]));
  };

  if (!data || data.alerts.length === 0) {
    return null;
  }

  const visibleAlerts = data.alerts.filter((a) => !dismissed.has(a.code));

  if (visibleAlerts.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-3">
      {visibleAlerts.map((alert) => (
        <AlertRow key={alert.code} alert={alert} onDismiss={handleDismiss} />
      ))}
    </div>
  );
}
