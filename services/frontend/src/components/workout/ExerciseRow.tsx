import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, Trash2 } from 'lucide-react';
import type { Exercise, UpdateExerciseRequest } from '../../types/exercise';
import { ALL_DAYS } from '../../lib/constants';
import { ExerciseEditor } from './ExerciseEditor';

interface ExerciseRowProps {
  exercise: Exercise;
  onUpdate: (id: number, data: UpdateExerciseRequest) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

export function ExerciseRow({ exercise, onUpdate, onDelete }: ExerciseRowProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-b border-border/50 last:border-b-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-2/50 transition-colors text-left"
      >
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-chalk truncate">{exercise.name}</p>
          <p className="text-xs text-steel font-mono mt-0.5">
            {exercise.sets}&times;{exercise.reps}
            {exercise.weight != null && exercise.weight > 0 && (
              <span className="text-ember ml-2">{exercise.weight} kg</span>
            )}
            {(exercise.weight == null || exercise.weight === 0) && (
              <span className="text-steel/60 ml-2">BW</span>
            )}
          </p>
        </div>
        <ChevronRight
          size={16}
          className={`text-steel shrink-0 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
        />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <ExerciseEditor
              exercise={exercise}
              days={['A', ...ALL_DAYS.filter(d => d !== 'A'), 'None']}
              onSave={async (data) => {
                await onUpdate(exercise.id, data);
                setExpanded(false);
              }}
              onCancel={() => setExpanded(false)}
            />
            <div className="px-4 pb-3">
              <button
                onClick={async () => {
                  if (confirm(`Delete "${exercise.name}"?`)) {
                    await onDelete(exercise.id);
                  }
                }}
                className="flex items-center gap-1.5 text-xs text-danger hover:text-danger/80 transition-colors"
              >
                <Trash2 size={12} />
                Delete exercise
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
