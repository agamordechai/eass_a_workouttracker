import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts';
import type { Exercise } from '../../types/exercise';

interface WorkoutDistributionProps {
  exercises: Exercise[];
}

export function WorkoutDistribution({ exercises }: WorkoutDistributionProps) {
  const days = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
  const data = days.map((day) => ({
    day: `Day ${day}`,
    count: exercises.filter((ex) => ex.workout_day === day).length,
  })).filter((d) => d.count > 0);

  if (data.length < 3) return null;

  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold text-text-primary mb-4">Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(63, 63, 70, 0.3)" />
          <PolarAngleAxis dataKey="day" tick={{ fill: '#71717a', fontSize: 11 }} />
          <Radar
            dataKey="count"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            fillOpacity={0.2}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
