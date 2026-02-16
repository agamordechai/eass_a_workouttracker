import { motion } from 'framer-motion';
import { Dumbbell, Layers, Weight } from 'lucide-react';
import { StatCard } from '../ui/StatCard';
import { containerStagger } from '../../lib/motion';
import type { Exercise } from '../../types/exercise';

interface StatsRowProps {
  exercises: Exercise[];
}

export function StatsRow({ exercises }: StatsRowProps) {
  const totalSets = exercises.reduce((sum, ex) => sum + ex.sets, 0);
  const totalVolume = exercises.reduce((sum, ex) => sum + ex.sets * ex.reps * (ex.weight || 0), 0);

  const formatVolume = (v: number) => {
    if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
    return v.toString();
  };

  return (
    <motion.div
      variants={containerStagger}
      initial="initial"
      animate="animate"
      className="grid grid-cols-3 gap-3"
    >
      <StatCard
        label="Exercises"
        value={exercises.length}
        icon={<Dumbbell size={18} />}
      />
      <StatCard
        label="Total Sets"
        value={totalSets}
        icon={<Layers size={18} />}
      />
      <StatCard
        label="Volume (kg)"
        value={formatVolume(totalVolume)}
        icon={<Weight size={18} />}
      />
    </motion.div>
  );
}
