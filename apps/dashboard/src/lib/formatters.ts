const DATE_FORMAT_OPTIONS: Intl.DateTimeFormatOptions = {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
};

/**
 * Formats an ISO date string to a human-readable label.
 * Example: "Apr 25, 2026 19:30"
 */
export function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString('en-US', DATE_FORMAT_OPTIONS);
}

const SECONDS_IN_MINUTE = 60;
const SECONDS_IN_HOUR = 3_600;

/**
 * Formats a duration in seconds to a human-readable relative string.
 * Examples: "2h 15m ago", "5m ago", "< 1m ago"
 */
export function formatDuration(seconds: number): string {
  if (seconds < SECONDS_IN_MINUTE) {
    return '< 1m ago';
  }

  if (seconds < SECONDS_IN_HOUR) {
    const minutes = Math.floor(seconds / SECONDS_IN_MINUTE);
    return `${minutes}m ago`;
  }

  const hours = Math.floor(seconds / SECONDS_IN_HOUR);
  const remainingMinutes = Math.floor((seconds % SECONDS_IN_HOUR) / SECONDS_IN_MINUTE);

  if (remainingMinutes === 0) {
    return `${hours}h ago`;
  }

  return `${hours}h ${remainingMinutes}m ago`;
}

/**
 * Formats a number using locale-aware separators.
 * Example: formatNumber(1234567.89, 2) → "1,234,567.89"
 */
export function formatNumber(n: number, decimals?: number): string {
  return n.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Formats a score rounded to 1 decimal place.
 * Example: formatScore(9.876) → "9.9"
 */
export function formatScore(n: number): string {
  return n.toFixed(1);
}
