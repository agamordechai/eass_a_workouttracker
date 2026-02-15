import { clsx } from 'clsx';
import { getDayColor } from '../../lib/constants';

interface BadgeProps {
  day: string;
  className?: string;
}

export function DayBadge({ day, className }: BadgeProps) {
  const colors = getDayColor(day);
  const label = day === 'None' ? 'Daily' : `Day ${day}`;
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border', colors.bg, colors.text, colors.border, className)}>
      {label}
    </span>
  );
}
