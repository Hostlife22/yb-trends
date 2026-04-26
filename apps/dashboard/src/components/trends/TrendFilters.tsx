import { useEffect, useRef } from 'react';
import { useForm, Controller, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import clsx from 'clsx';

const filterSchema = z.object({
  contentType: z.enum(['all', 'movie', 'animation']),
  studio: z.string(),
  minScore: z.number().min(0),
});

export type FilterValues = z.infer<typeof filterSchema>;

interface TrendFiltersProps {
  onFilterChange: (filters: FilterValues) => void;
  totalCount: number;
  filteredCount: number;
}

const DEFAULT_VALUES: FilterValues = {
  contentType: 'all',
  studio: '',
  minScore: 0,
};

const DEBOUNCE_DELAY_MS = 300;

const inputClass = clsx(
  'rounded-lg px-3 py-2 text-sm text-white',
  'bg-white/5 border border-white/10',
  'placeholder:text-gray-600',
  'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
  'transition-colors duration-150',
);

export default function TrendFilters({
  onFilterChange,
  totalCount,
  filteredCount,
}: TrendFiltersProps) {
  const { control, register } = useForm<FilterValues>({
    resolver: zodResolver(filterSchema),
    defaultValues: DEFAULT_VALUES,
  });

  const contentType = useWatch({ control, name: 'contentType' });
  const studio = useWatch({ control, name: 'studio' });
  const minScore = useWatch({ control, name: 'minScore' });

  const onFilterChangeRef = useRef(onFilterChange);
  useEffect(() => {
    onFilterChangeRef.current = onFilterChange;
  }, [onFilterChange]);

  useEffect(() => {
    const timer = setTimeout(() => {
      onFilterChangeRef.current({ contentType, studio, minScore });
    }, DEBOUNCE_DELAY_MS);

    return () => clearTimeout(timer);
  }, [contentType, studio, minScore]);

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Type
          </label>
          <Controller
            name="contentType"
            control={control}
            render={({ field }) => (
              <select
                {...field}
                className={clsx(inputClass, 'pr-8 appearance-none cursor-pointer')}
              >
                <option value="all" className="bg-gray-900">
                  All types
                </option>
                <option value="movie" className="bg-gray-900">
                  Movie
                </option>
                <option value="animation" className="bg-gray-900">
                  Animation
                </option>
              </select>
            )}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Studio
          </label>
          <input
            {...register('studio')}
            type="text"
            placeholder="Search studio..."
            className={clsx(inputClass, 'w-48')}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Min Score
          </label>
          <input
            {...register('minScore', { valueAsNumber: true })}
            type="number"
            min={0}
            step={1}
            placeholder="0"
            className={clsx(inputClass, 'w-24')}
          />
        </div>
      </div>

      <p className="text-sm text-gray-500 shrink-0">
        Showing{' '}
        <span className="font-medium text-gray-300">{filteredCount}</span> of{' '}
        <span className="font-medium text-gray-300">{totalCount}</span> trends
      </p>
    </div>
  );
}
