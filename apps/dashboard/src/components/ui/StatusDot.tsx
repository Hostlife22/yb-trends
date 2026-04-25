import clsx from 'clsx';

type DotStatus = 'healthy' | 'warning' | 'critical';

interface StatusDotProps {
  status: DotStatus;
  pulse?: boolean;
}

const STATUS_CLASSES: Record<DotStatus, string> = {
  healthy: 'bg-emerald-500',
  warning: 'bg-amber-400',
  critical: 'bg-red-500',
};

const PULSE_CLASSES: Record<DotStatus, string> = {
  healthy: 'animate-ping bg-emerald-500',
  warning: 'animate-ping bg-amber-400',
  critical: 'animate-ping bg-red-500',
};

export default function StatusDot({ status, pulse = false }: StatusDotProps) {
  return (
    <span className="relative flex h-2.5 w-2.5 shrink-0">
      {pulse && (
        <span
          className={clsx(
            'absolute inline-flex h-full w-full rounded-full opacity-75',
            PULSE_CLASSES[status],
          )}
        />
      )}
      <span
        className={clsx(
          'relative inline-flex h-2.5 w-2.5 rounded-full',
          STATUS_CLASSES[status],
        )}
      />
    </span>
  );
}
