/**
 * Returns a new sorted array without mutating the original.
 * Handles string and number comparisons.
 */
export function sortBy<T>(
  items: T[],
  key: keyof T,
  direction: 'asc' | 'desc',
): T[] {
  return [...items].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];

    let comparison: number;

    if (typeof aVal === 'string' && typeof bVal === 'string') {
      comparison = aVal.localeCompare(bVal);
    } else if (typeof aVal === 'number' && typeof bVal === 'number') {
      comparison = aVal - bVal;
    } else {
      comparison = String(aVal).localeCompare(String(bVal));
    }

    return direction === 'asc' ? comparison : -comparison;
  });
}
