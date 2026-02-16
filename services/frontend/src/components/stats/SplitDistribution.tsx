import { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { getDayColor } from '../../lib/constants';
import type { Exercise } from '../../types/exercise';

interface SplitDistributionProps {
  exercises: Exercise[];
}

export function SplitDistribution({ exercises }: SplitDistributionProps) {
  const data = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const ex of exercises) {
      const day = (!ex.workout_day || ex.workout_day === 'None') ? 'Daily' : ex.workout_day;
      counts[day] = (counts[day] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([day, count]) => ({ day, count }))
      .sort((a, b) => b.count - a.count);
  }, [exercises]);

  if (data.length === 0) return null;

  return (
    <div className="card">
      <h3 className="text-sm font-bold text-chalk mb-4">Split Distribution</h3>
      <div className="h-40 flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="day"
              cx="50%"
              cy="50%"
              innerRadius={35}
              outerRadius={60}
              paddingAngle={3}
              strokeWidth={0}
            >
              {data.map((entry) => (
                <Cell key={entry.day} fill={getDayColor(entry.day).hex} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1C1917',
                border: '1px solid rgba(87,83,78,0.4)',
                borderRadius: '12px',
                color: '#FAFAF9',
                fontSize: '12px',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-2 mt-2 justify-center">
        {data.map(({ day, count }) => (
          <div key={day} className="flex items-center gap-1.5 text-xs text-steel">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getDayColor(day).hex }} />
            {day} ({count})
          </div>
        ))}
      </div>
    </div>
  );
}
