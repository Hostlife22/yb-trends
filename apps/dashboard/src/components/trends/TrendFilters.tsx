import { useEffect, useRef } from 'react';
import { useForm, Controller, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import clsx from 'clsx';

const sortBySchema = z.enum([
  'final_score',
  'search_demand',
  'search_momentum',
  'youtube_demand',
  'youtube_freshness',
  'youtube_median_views_14d',
  'youtube_total_views_14d',
]);

export type SortBy = z.infer<typeof sortBySchema>;

const filterSchema = z.object({
  contentType: z.enum(['all', 'movie', 'animation']),
  studio: z.string(),
  minScore: z.number().min(0),
  language: z.string(),
  country: z.string(),
  minYear: z.number().nullable(),
  maxYear: z.number().nullable(),
  sortBy: sortBySchema,
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
  language: '',
  country: '',
  minYear: null,
  maxYear: null,
  sortBy: 'final_score',
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
  const language = useWatch({ control, name: 'language' });
  const country = useWatch({ control, name: 'country' });
  const minYear = useWatch({ control, name: 'minYear' });
  const maxYear = useWatch({ control, name: 'maxYear' });
  const sortByValue = useWatch({ control, name: 'sortBy' });

  const onFilterChangeRef = useRef(onFilterChange);
  useEffect(() => {
    onFilterChangeRef.current = onFilterChange;
  }, [onFilterChange]);

  useEffect(() => {
    const timer = setTimeout(() => {
      onFilterChangeRef.current({
        contentType,
        studio,
        minScore,
        language,
        country,
        minYear,
        maxYear,
        sortBy: sortByValue,
      });
    }, DEBOUNCE_DELAY_MS);

    return () => clearTimeout(timer);
  }, [contentType, studio, minScore, language, country, minYear, maxYear, sortByValue]);

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

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Language
          </label>
          <input
            {...register('language')}
            type="text"
            placeholder="en, es, ja…"
            maxLength={5}
            className={clsx(inputClass, 'w-24 uppercase')}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Country
          </label>
          <input
            {...register('country')}
            type="text"
            placeholder="US, JP…"
            maxLength={2}
            className={clsx(inputClass, 'w-20 uppercase')}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Min Year
          </label>
          <input
            {...register('minYear', {
              setValueAs: (v) => (v === '' || v === null ? null : Number(v)),
            })}
            type="number"
            min={1900}
            max={2100}
            step={1}
            placeholder="—"
            className={clsx(inputClass, 'w-24')}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Max Year
          </label>
          <input
            {...register('maxYear', {
              setValueAs: (v) => (v === '' || v === null ? null : Number(v)),
            })}
            type="number"
            min={1900}
            max={2100}
            step={1}
            placeholder="—"
            className={clsx(inputClass, 'w-24')}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Sort by
          </label>
          <Controller
            name="sortBy"
            control={control}
            render={({ field }) => (
              <select
                {...field}
                className={clsx(inputClass, 'pr-8 appearance-none cursor-pointer')}
              >
                <option value="final_score" className="bg-gray-900">Final score</option>
                <option value="search_demand" className="bg-gray-900">Search demand</option>
                <option value="search_momentum" className="bg-gray-900">Search momentum</option>
                <option value="youtube_demand" className="bg-gray-900">YouTube demand</option>
                <option value="youtube_freshness" className="bg-gray-900">YouTube freshness</option>
                <option value="youtube_median_views_14d" className="bg-gray-900">YT median views</option>
                <option value="youtube_total_views_14d" className="bg-gray-900">YT total views</option>
              </select>
            )}
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
