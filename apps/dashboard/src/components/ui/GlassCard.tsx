import clsx from 'clsx';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export default function GlassCard({ children, className, onClick }: GlassCardProps) {
  return (
    <div
      className={clsx(
        'bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6',
        className,
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
