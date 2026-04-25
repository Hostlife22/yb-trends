import clsx from 'clsx';

interface ScoreBarProps {
  score: number;
  max?: number;
  className?: string;
}

export default function ScoreBar({ score, max = 200, className }: ScoreBarProps) {
  const clampedScore = Math.min(Math.max(score, 0), max);
  const widthPercent = (clampedScore / max) * 100;

  return (
    <div
      className={clsx(
        'h-1.5 w-full overflow-hidden rounded-full bg-white/10',
        className,
      )}
    >
      <div
        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
        style={{ width: `${widthPercent}%` }}
      />
    </div>
  );
}
