import { clsx } from 'clsx';
import { getDayColor } from '../../lib/constants';
import type { Exercise } from '../../types/exercise';

const DAYS = ['All', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'None'];

interface WorkoutDayTabsProps {
  exercises: Exercise[];
  activeDay: string;
  onDayChange: (day: string) => void;
}

export function WorkoutDayTabs({ exercises, activeDay, onDayChange }: WorkoutDayTabsProps) {
  const counts = DAYS.reduce<Record<string, number>>((acc, day) => {
    acc[day] = day === 'All'
      ? exercises.length
      : exercises.filter((ex) => ex.workout_day === day).length;
    return acc;
  }, {});

  return (
    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
      {DAYS.map((day) => {
        const isActive = activeDay === day;
        const colors = day !== 'All' ? getDayColor(day) : null;
        const label = day === 'None' ? 'Daily' : day === 'All' ? 'All' : `Day ${day}`;

        return (
          <button
            key={day}
            onClick={() => onDayChange(day)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border',
              isActive
                ? colors
                  ? `${colors.bg} ${colors.text} ${colors.border}`
                  : 'bg-primary-muted text-primary border-primary/30'
                : 'bg-transparent text-text-muted border-transparent hover:bg-surface-light hover:text-text-secondary'
            )}
          >
            {label}
            {counts[day] > 0 && (
              <span className={clsx(
                'text-[10px] px-1.5 py-0.5 rounded-full',
                isActive ? 'bg-white/10' : 'bg-surface-light'
              )}>
                {counts[day]}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
