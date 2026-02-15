import { motion } from 'framer-motion';
import { ChevronRight } from 'lucide-react';
import { DayBadge } from '../ui/Badge';
import type { Exercise } from '../../types/exercise';

interface ExerciseCardProps {
  exercise: Exercise;
  onClick: () => void;
  index: number;
}

export function ExerciseCard({ exercise, onClick, index }: ExerciseCardProps) {
  return (
    <motion.button
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, duration: 0.25 }}
      onClick={onClick}
      className="card hover:border-primary/30 transition-all text-left flex items-center gap-4 p-4 w-full"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <DayBadge day={exercise.workout_day} />
          <h3 className="text-sm font-semibold text-text-primary truncate">{exercise.name}</h3>
        </div>
        <p className="text-xs text-text-secondary">
          {exercise.sets} sets &times; {exercise.reps} reps
          {exercise.weight !== null && (
            <span className="ml-2 text-energy font-medium">{exercise.weight} kg</span>
          )}
          {exercise.weight === null && (
            <span className="ml-2 text-text-muted">Bodyweight</span>
          )}
        </p>
      </div>
      <ChevronRight size={16} className="text-text-muted shrink-0" />
    </motion.button>
  );
}
