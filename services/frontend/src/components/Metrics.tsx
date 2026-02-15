import type { Exercise } from '../types/exercise';

interface MetricsProps {
  exercises: Exercise[];
}

export function Metrics({ exercises }: MetricsProps) {
  const totalExercises = exercises.length;
  const totalSets = exercises.reduce((sum, ex) => sum + ex.sets, 0);
  const totalVolume = exercises.reduce((sum, ex) => {
    if (ex.weight !== null) return sum + ex.sets * ex.reps * ex.weight;
    return sum;
  }, 0);
  const weightedExercises = exercises.filter((ex) => ex.weight !== null).length;

  const metrics = [
    { label: 'Exercises', value: totalExercises, color: 'text-primary' },
    { label: 'Total Sets', value: totalSets, color: 'text-[#4FBCFF]' },
    { label: 'Volume', value: `${totalVolume.toFixed(0)} kg`, color: 'text-[#46D160]' },
    { label: 'Weighted', value: weightedExercises, color: 'text-amber-400' },
  ];

  return (
    <div className="card flex items-center justify-around py-3">
      {metrics.map(({ label, value, color }, idx) => (
        <div key={label} className="flex items-center gap-2">
          {idx > 0 && <div className="w-px h-8 bg-border -ml-1 mr-1" />}
          <div className="text-center">
            <div className={`text-base font-bold ${color}`}>{value}</div>
            <div className="text-[11px] text-text-muted">{label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
