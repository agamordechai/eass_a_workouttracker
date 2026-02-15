import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { Exercise } from '../../types/exercise';

const DAY_CHART_COLORS: Record<string, string> = {
  A: '#8b5cf6', B: '#3b82f6', C: '#10b981', D: '#f97316',
  E: '#ec4899', F: '#f59e0b', G: '#06b6d4', None: '#71717a',
};

interface VolumeChartProps {
  exercises: Exercise[];
}

export function VolumeChart({ exercises }: VolumeChartProps) {
  const days = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'None'];
  const data = days.map((day) => {
    const dayExercises = exercises.filter((ex) => ex.workout_day === day);
    const volume = dayExercises.reduce((sum, ex) => {
      if (ex.weight !== null) return sum + ex.sets * ex.reps * ex.weight;
      return sum;
    }, 0);
    return { day: day === 'None' ? 'Daily' : `Day ${day}`, volume: Math.round(volume), key: day };
  }).filter((d) => d.volume > 0);

  if (data.length === 0) return null;

  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold text-text-primary mb-4">Volume by Day</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <XAxis dataKey="day" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} width={50} />
          <Tooltip
            contentStyle={{
              background: 'rgba(24, 24, 27, 0.9)',
              border: '1px solid rgba(63, 63, 70, 0.5)',
              borderRadius: '0.5rem',
              backdropFilter: 'blur(8px)',
              color: '#fafafa',
              fontSize: '12px',
            }}
            formatter={(value) => [`${Number(value).toLocaleString()} kg`, 'Volume']}
          />
          <Bar dataKey="volume" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.key} fill={DAY_CHART_COLORS[entry.key] || '#71717a'} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
