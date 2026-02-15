import { Dumbbell, Layers, Weight, Flame } from 'lucide-react';
import { ProgressRing } from '../ui/ProgressRing';
import type { Exercise } from '../../types/exercise';

interface MetricsGridProps {
  exercises: Exercise[];
}

export function MetricsGrid({ exercises }: MetricsGridProps) {
  const totalExercises = exercises.length;
  const totalSets = exercises.reduce((sum, ex) => sum + ex.sets, 0);
  const totalVolume = exercises.reduce((sum, ex) => {
    if (ex.weight !== null) return sum + ex.sets * ex.reps * ex.weight;
    return sum;
  }, 0);
  const weightedExercises = exercises.filter((ex) => ex.weight !== null).length;

  const metrics = [
    { label: 'Exercises', value: totalExercises, icon: Dumbbell, color: '#8b5cf6', max: 50 },
    { label: 'Total Sets', value: totalSets, icon: Layers, color: '#3b82f6', max: 200 },
    { label: 'Volume', value: Math.round(totalVolume), icon: Weight, color: '#22c55e', max: 50000, suffix: ' kg' },
    { label: 'Weighted', value: weightedExercises, icon: Flame, color: '#f97316', max: totalExercises || 1 },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {metrics.map(({ label, value, icon: Icon, color, max, suffix }) => (
        <div key={label} className="card flex items-center gap-3 p-4">
          <ProgressRing value={value} max={max} color={color} size={44} strokeWidth={3} />
          <div className="min-w-0">
            <div className="text-lg font-bold text-text-primary">{value.toLocaleString()}{suffix}</div>
            <div className="text-xs text-text-muted flex items-center gap-1">
              <Icon size={12} style={{ color }} />
              {label}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
