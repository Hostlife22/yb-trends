import clsx from 'clsx';

type BadgeVariant = 'movie' | 'animation' | 'warning' | 'critical' | 'success' | 'unknown';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  movie: 'bg-blue-500/20 text-blue-400',
  animation: 'bg-purple-500/20 text-purple-400',
  warning: 'bg-amber-500/20 text-amber-400',
  critical: 'bg-red-500/20 text-red-400',
  success: 'bg-emerald-500/20 text-emerald-400',
  unknown: 'bg-gray-500/20 text-gray-400',
};

export default function Badge({ variant, children }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        VARIANT_CLASSES[variant],
      )}
    >
      {children}
    </span>
  );
}
