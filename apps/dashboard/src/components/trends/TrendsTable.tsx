import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronUp, ChevronDown } from 'lucide-react';
import clsx from 'clsx';
import type { ClassifiedTrendItem } from '@/api/types';
import { sortBy } from '@/lib/sort';
import TrendRow from './TrendRow';

interface TrendsTableProps {
  items: ClassifiedTrendItem[];
}

type SortKey = keyof ClassifiedTrendItem;
type SortDirection = 'asc' | 'desc';

interface ColumnDef {
  label: string;
  key: SortKey;
  align?: 'left' | 'right';
}

const COLUMNS: ColumnDef[] = [
  { label: '#', key: 'query', align: 'left' },
  { label: 'Title', key: 'title_normalized', align: 'left' },
  { label: 'Type', key: 'content_type', align: 'left' },
  { label: 'Studio', key: 'studio', align: 'left' },
  { label: 'Score', key: 'final_score', align: 'left' },
  { label: 'Interest', key: 'interest_level', align: 'right' },
  { label: 'Growth', key: 'growth_velocity', align: 'left' },
  { label: 'Confidence', key: 'confidence', align: 'right' },
] as const;

export default function TrendsTable({ items }: TrendsTableProps) {
  const navigate = useNavigate();
  const [sortKey, setSortKey] = useState<SortKey>('final_score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  function handleHeaderClick(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDirection('desc');
    }
  }

  function handleRowClick(item: ClassifiedTrendItem) {
    navigate(`/trends/${encodeURIComponent(item.query)}`);
  }

  const sortedItems = sortBy(items, sortKey, sortDirection);

  return (
    <div className="overflow-hidden rounded-2xl bg-white/5 border border-white/10">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-white/10">
              {COLUMNS.map((col, colIndex) => {
                const isActive = sortKey === col.key;
                const isRankCol = colIndex === 0;

                return (
                  <th
                    key={col.key}
                    scope="col"
                    className={clsx(
                      'py-3 text-xs font-medium uppercase tracking-wider select-none',
                      colIndex === 0 ? 'pl-4 pr-3' : 'px-3',
                      colIndex === COLUMNS.length - 1 && 'pr-4',
                      col.align === 'right' ? 'text-right' : 'text-left',
                      isRankCol
                        ? 'text-gray-600 w-10'
                        : 'text-gray-500 cursor-pointer hover:text-gray-300 transition-colors duration-150',
                      isActive && !isRankCol && 'text-indigo-400',
                    )}
                    onClick={isRankCol ? undefined : () => handleHeaderClick(col.key)}
                  >
                    {isRankCol ? (
                      col.label
                    ) : (
                      <span className="inline-flex items-center gap-1">
                        {col.label}
                        {isActive && (
                          sortDirection === 'asc' ? (
                            <ChevronUp size={12} />
                          ) : (
                            <ChevronDown size={12} />
                          )
                        )}
                      </span>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {sortedItems.map((item, index) => (
              <TrendRow
                key={item.query}
                item={item}
                rank={index + 1}
                onClick={() => handleRowClick(item)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
