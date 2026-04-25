import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: number;
  className?: string;
}

export default function Spinner({ size = 20, className }: SpinnerProps) {
  return (
    <Loader2
      size={size}
      className={clsx('animate-spin text-indigo-400', className)}
    />
  );
}
