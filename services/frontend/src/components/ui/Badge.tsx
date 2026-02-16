import { getDayColor } from '../../lib/constants';

interface BadgeProps {
  day: string;
  size?: 'sm' | 'md';
}

export function Badge({ day, size = 'sm' }: BadgeProps) {
  const color = getDayColor(day);
  const sizeClass = size === 'md' ? 'px-3 py-1 text-xs' : 'px-2 py-0.5 text-[11px]';

  return (
    <span className={`inline-flex items-center rounded-lg font-semibold ${sizeClass} ${color.bg} ${color.text} border ${color.border}`}>
      {day}
    </span>
  );
}
