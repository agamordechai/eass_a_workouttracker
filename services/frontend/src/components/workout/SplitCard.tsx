import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Plus } from 'lucide-react';
import { getDayColor, DAY_LABELS } from '../../lib/constants';
import type { Exercise, UpdateExerciseRequest } from '../../types/exercise';
import { ExerciseRow } from './ExerciseRow';

interface SplitCardProps {
  day: string;
  exercises: Exercise[];
  onUpdate: (id: number, data: UpdateExerciseRequest) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onAddToDay: (day: string) => void;
}

export function SplitCard({ day, exercises, onUpdate, onDelete, onAddToDay }: SplitCardProps) {
  const [collapsed, setCollapsed] = useState(false);
  const color = getDayColor(day);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-0 overflow-hidden"
    >
      {/* Colored accent bar + header */}
      <div className="flex items-center">
        <div className={`w-1 self-stretch ${color.accent} rounded-l-2xl`} />
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex-1 flex items-center gap-3 px-4 py-3 hover:bg-surface-2/30 transition-colors"
        >
          <div className={`w-2.5 h-2.5 rounded-full ${color.accent}`} />
          <span className="text-sm font-bold text-chalk flex-1 text-left">
            {DAY_LABELS[day] || day}
          </span>
          <span className="text-xs text-steel font-mono">
            {exercises.length} exercise{exercises.length !== 1 ? 's' : ''}
          </span>
          <ChevronDown
            size={16}
            className={`text-steel transition-transform duration-200 ${collapsed ? '-rotate-90' : ''}`}
          />
        </button>
      </div>

      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="ml-1">
              {exercises.map((ex) => (
                <ExerciseRow
                  key={ex.id}
                  exercise={ex}
                  onUpdate={onUpdate}
                  onDelete={onDelete}
                />
              ))}

              <button
                onClick={() => onAddToDay(day)}
                className={`w-full flex items-center gap-2 px-4 py-2.5 text-xs font-medium ${color.text} hover:bg-surface-2/30 transition-colors`}
              >
                <Plus size={14} />
                Add to {DAY_LABELS[day] || day}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
