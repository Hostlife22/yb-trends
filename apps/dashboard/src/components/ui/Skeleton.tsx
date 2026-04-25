import clsx from 'clsx';

type SkeletonVariant = 'text' | 'card' | 'row';

interface SkeletonProps {
  className?: string;
  variant?: SkeletonVariant;
}

const VARIANT_CLASSES: Record<SkeletonVariant, string> = {
  text: 'h-4 w-full rounded',
  card: 'h-32 w-full rounded-2xl',
  row: 'h-10 w-full rounded-xl',
};

export default function Skeleton({ className, variant = 'text' }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-white/10',
        VARIANT_CLASSES[variant],
        className,
      )}
    />
  );
}
