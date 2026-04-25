import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import clsx from 'clsx';
import { useSync } from '@/hooks/use-sync';
import GlassCard from '@/components/ui/GlassCard';
import SyncButton from './SyncButton';

const syncFormSchema = z.object({
  region: z.string().min(1, 'Region is required'),
  period: z.enum(['7d', '14d', '30d']),
});

type SyncFormValues = z.infer<typeof syncFormSchema>;

const DEFAULT_VALUES: SyncFormValues = {
  region: 'US',
  period: '7d',
};

const PERIOD_OPTIONS = [
  { value: '7d', label: '7 days' },
  { value: '14d', label: '14 days' },
  { value: '30d', label: '30 days' },
] as const;

const INPUT_BASE_CLASSES =
  'w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors';

export default function SyncForm() {
  const { mutate, isPending, data, error } = useSync();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SyncFormValues>({
    resolver: zodResolver(syncFormSchema),
    defaultValues: DEFAULT_VALUES,
  });

  const onSubmit = (values: SyncFormValues) => {
    mutate({ region: values.region, period: values.period });
  };

  return (
    <GlassCard>
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div className="flex flex-col gap-5">
          <h2 className="text-base font-semibold text-gray-100">Run Sync</h2>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="sync-region"
              className="text-xs font-medium text-gray-400"
            >
              Region
            </label>
            <input
              id="sync-region"
              type="text"
              placeholder="e.g. US"
              className={clsx(
                INPUT_BASE_CLASSES,
                errors.region && 'border-red-500/50',
              )}
              disabled={isPending}
              {...register('region')}
            />
            {errors.region && (
              <p className="text-xs text-red-400">{errors.region.message}</p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="sync-period"
              className="text-xs font-medium text-gray-400"
            >
              Period
            </label>
            <select
              id="sync-period"
              className={clsx(
                INPUT_BASE_CLASSES,
                'cursor-pointer',
                errors.period && 'border-red-500/50',
              )}
              disabled={isPending}
              {...register('period')}
            >
              {PERIOD_OPTIONS.map((opt) => (
                <option
                  key={opt.value}
                  value={opt.value}
                  className="bg-slate-900 text-white"
                >
                  {opt.label}
                </option>
              ))}
            </select>
            {errors.period && (
              <p className="text-xs text-red-400">{errors.period.message}</p>
            )}
          </div>

          <SyncButton
            isPending={isPending}
            data={data ?? undefined}
            error={error}
            onTrigger={() => {
              /* submit is handled by the form's onSubmit via type="submit" */
            }}
          />
        </div>
      </form>
    </GlassCard>
  );
}
