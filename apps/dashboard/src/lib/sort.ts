/**
 * Returns a new sorted array without mutating the original.
 * Handles string, number, and boolean comparisons; falls back to string compare.
 */
export function sortBy<T>(
  items: readonly T[],
  key: keyof T,
  direction: 'asc' | 'desc',
): T[] {
  const factor = direction === 'asc' ? 1 : -1;

  return [...items].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];

    if (aVal == null && bVal == null) return 0;
    if (aVal == null) return 1;
    if (bVal == null) return -1;

    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return aVal.localeCompare(bVal) * factor;
    }
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return (aVal - bVal) * factor;
    }
    if (typeof aVal === 'boolean' && typeof bVal === 'boolean') {
      return (Number(aVal) - Number(bVal)) * factor;
    }
    return String(aVal).localeCompare(String(bVal)) * factor;
  });
}
