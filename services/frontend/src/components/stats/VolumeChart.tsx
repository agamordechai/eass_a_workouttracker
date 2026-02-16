import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { getDayColor } from '../../lib/constants';
import type { Exercise } from '../../types/exercise';

interface VolumeChartProps {
  exercises: Exercise[];
}

export function VolumeChart({ exercises }: VolumeChartProps) {
  const data = useMemo(() => {
    const byDay: Record<string, number> = {};
    for (const ex of exercises) {
      const day = (!ex.workout_day || ex.workout_day === 'None') ? 'Daily' : ex.workout_day;
      byDay[day] = (byDay[day] || 0) + ex.sets * ex.reps * (ex.weight || 0);
    }
    return Object.entries(byDay)
      .map(([day, volume]) => ({ day, volume: Math.round(volume) }))
      .sort((a, b) => b.volume - a.volume);
  }, [exercises]);

  if (data.length === 0) return null;

  return (
    <div className="card">
      <h3 className="text-sm font-bold text-chalk mb-4">Volume by Day</h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barCategoryGap="20%">
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#94A3B8', fontSize: 11 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#94A3B8', fontSize: 11 }}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1C1917',
                border: '1px solid rgba(87,83,78,0.4)',
                borderRadius: '12px',
                color: '#FAFAF9',
                fontSize: '12px',
              }}
              formatter={(value) => [`${Number(value).toLocaleString()} kg`, 'Volume']}
            />
            <Bar dataKey="volume" radius={[6, 6, 0, 0]}>
              {data.map((entry) => (
                <Cell key={entry.day} fill={getDayColor(entry.day).hex} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
