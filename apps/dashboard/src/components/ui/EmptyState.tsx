import { type LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
}

export default function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      {Icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/5">
          <Icon size={24} className="text-gray-500" strokeWidth={1.5} />
        </div>
      )}
      <p className="text-sm font-medium text-gray-300">{title}</p>
      {description && (
        <p className="max-w-xs text-xs leading-relaxed text-gray-500">{description}</p>
      )}
    </div>
  );
}
