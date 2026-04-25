import { AlertTriangle } from 'lucide-react';
import Button from './Button';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 backdrop-blur-xl">
      <AlertTriangle
        size={18}
        className="mt-0.5 shrink-0 text-red-400"
        aria-hidden="true"
      />
      <p className="flex-1 text-sm text-red-300">{message}</p>
      {onRetry && (
        <Button
          variant="danger"
          size="sm"
          onClick={onRetry}
          className="shrink-0"
        >
          Retry
        </Button>
      )}
    </div>
  );
}
