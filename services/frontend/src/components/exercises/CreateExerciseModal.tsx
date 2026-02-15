import { useState, FormEvent } from 'react';
import { Modal } from '../ui/Modal';
import { getDayColor } from '../../lib/constants';
import { clsx } from 'clsx';
import type { CreateExerciseRequest } from '../../types/exercise';

const DAYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'None'];

interface CreateExerciseModalProps {
  open: boolean;
  onSubmit: (data: CreateExerciseRequest) => Promise<void>;
  onClose: () => void;
}

export function CreateExerciseModal({ open, onSubmit, onClose }: CreateExerciseModalProps) {
  const [name, setName] = useState('');
  const [sets, setSets] = useState(3);
  const [reps, setReps] = useState(10);
  const [weight, setWeight] = useState('');
  const [workoutDay, setWorkoutDay] = useState('A');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Exercise name is required!');
      return;
    }

    let weightValue: number | null = null;
    if (weight.trim()) {
      const parsed = parseFloat(weight);
      if (isNaN(parsed) || parsed <= 0) {
        setError('Weight must be a valid positive number or empty for bodyweight');
        return;
      }
      weightValue = parsed;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        sets,
        reps,
        weight: weightValue,
        workout_day: workoutDay,
      });
      setName('');
      setSets(3);
      setReps(10);
      setWeight('');
      setWorkoutDay('A');
      onClose();
    } catch (err) {
      setError(`Failed to create exercise: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Exercise" description="Add a new exercise to your routine">
      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded-lg px-3 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="create-name" className="block text-xs font-medium text-text-secondary mb-1.5">Exercise Name *</label>
          <input id="create-name" type="text" placeholder="e.g., Bench Press" value={name} onChange={(e) => setName(e.target.value)} disabled={isSubmitting} className="input" autoFocus />
        </div>

        {/* Day selector pills */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">Workout Day *</label>
          <div className="flex flex-wrap gap-1.5">
            {DAYS.map((day) => {
              const colors = getDayColor(day);
              const isActive = workoutDay === day;
              return (
                <button
                  key={day}
                  type="button"
                  onClick={() => setWorkoutDay(day)}
                  className={clsx(
                    'px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all',
                    isActive
                      ? `${colors.bg} ${colors.text} ${colors.border}`
                      : 'bg-surface-light border-border text-text-muted hover:text-text-secondary'
                  )}
                >
                  {day === 'None' ? 'Daily' : `Day ${day}`}
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label htmlFor="create-sets" className="block text-xs font-medium text-text-secondary mb-1.5">Sets *</label>
            <input id="create-sets" type="number" min={1} max={20} value={sets} onChange={(e) => setSets(parseInt(e.target.value) || 1)} disabled={isSubmitting} className="input" />
          </div>
          <div>
            <label htmlFor="create-reps" className="block text-xs font-medium text-text-secondary mb-1.5">Reps *</label>
            <input id="create-reps" type="number" min={1} max={100} value={reps} onChange={(e) => setReps(parseInt(e.target.value) || 1)} disabled={isSubmitting} className="input" />
          </div>
          <div>
            <label htmlFor="create-weight" className="block text-xs font-medium text-text-secondary mb-1.5">Weight (kg)</label>
            <input id="create-weight" type="text" placeholder="BW" value={weight} onChange={(e) => setWeight(e.target.value)} disabled={isSubmitting} className="input" />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button type="submit" className="btn btn-primary flex-1" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Exercise'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </button>
        </div>
      </form>
    </Modal>
  );
}
