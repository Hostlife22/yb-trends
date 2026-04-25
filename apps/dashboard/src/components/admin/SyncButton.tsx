import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import { useSync } from '@/hooks/use-sync';
import Button from '@/components/ui/Button';
import type { SyncResponse } from '@/api/types';

interface SyncButtonProps {
  /** When provided, the button is controlled by a parent (e.g. SyncForm). */
  isPending?: boolean;
  data?: SyncResponse;
  error?: Error | null;
  onTrigger?: () => void;
}

const SUCCESS_DISPLAY_DURATION_MS = 3_000;

export default function SyncButton({
  isPending: externalIsPending,
  data: externalData,
  error: externalError,
  onTrigger,
}: SyncButtonProps = {}) {
  const sync = useSync();

  const isControlled = onTrigger !== undefined;
  const isPending = isControlled ? (externalIsPending ?? false) : sync.isPending;
  const data = isControlled ? externalData : sync.data;
  const error = isControlled ? externalError : sync.error;

  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (!data) return;

    setShowSuccess(true);
    const timerId = setTimeout(() => {
      setShowSuccess(false);
    }, SUCCESS_DISPLAY_DURATION_MS);

    return () => clearTimeout(timerId);
  }, [data]);

  const handleClick = () => {
    if (isControlled) {
      onTrigger();
    } else {
      sync.mutate({});
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <Button
        type={isControlled ? 'submit' : 'button'}
        variant="primary"
        loading={isPending}
        onClick={isControlled ? undefined : handleClick}
        disabled={isPending}
      >
        {showSuccess && !isPending ? (
          <>
            <Check size={14} aria-hidden="true" />
            Saved {data?.saved ?? 0} items
          </>
        ) : (
          'Trigger Sync'
        )}
      </Button>

      {error && (
        <p className="text-xs text-red-400">{error.message}</p>
      )}
    </div>
  );
}
