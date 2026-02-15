import { useState, FormEvent, useEffect } from 'react';
import { Trash2 } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { getDayColor } from '../../lib/constants';
import { clsx } from 'clsx';
import type { Exercise, UpdateExerciseRequest } from '../../types/exercise';

const DAYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'None'];

interface EditExerciseModalProps {
  exercise: Exercise | null;
  open: boolean;
  onSubmit: (exerciseId: number, data: UpdateExerciseRequest) => Promise<void>;
  onCancel: () => void;
  onDelete?: (exerciseId: number) => void;
}

export function EditExerciseModal({ exercise, open, onSubmit, onCancel, onDelete }: EditExerciseModalProps) {
  const [name, setName] = useState('');
  const [sets, setSets] = useState(3);
  const [reps, setReps] = useState(10);
  const [weight, setWeight] = useState('');
  const [workoutDay, setWorkoutDay] = useState('A');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (exercise) {
      setName(exercise.name);
      setSets(exercise.sets);
      setReps(exercise.reps);
      setWeight(exercise.weight !== null ? String(exercise.weight) : '');
      setWorkoutDay(exercise.workout_day);
      setError('');
      setConfirmDelete(false);
    }
  }, [exercise]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!exercise) return;
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
      await onSubmit(exercise.id, {
        name: name.trim(),
        sets,
        reps,
        weight: weightValue,
        workout_day: workoutDay,
      });
      onCancel();
    } catch (err) {
      setError(`Failed to update exercise: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!exercise) return null;

  return (
    <Modal
      open={open}
      onClose={onCancel}
      title="Edit Exercise"
      description={`Updating: ${exercise.name}`}
    >
      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded-lg px-3 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="edit-name" className="block text-xs font-medium text-text-secondary mb-1.5">Exercise Name *</label>
          <input id="edit-name" type="text" value={name} onChange={(e) => setName(e.target.value)} disabled={isSubmitting} className="input" />
        </div>

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
            <label htmlFor="edit-sets" className="block text-xs font-medium text-text-secondary mb-1.5">Sets *</label>
            <input id="edit-sets" type="number" min={1} max={20} value={sets} onChange={(e) => setSets(parseInt(e.target.value) || 1)} disabled={isSubmitting} className="input" />
          </div>
          <div>
            <label htmlFor="edit-reps" className="block text-xs font-medium text-text-secondary mb-1.5">Reps *</label>
            <input id="edit-reps" type="number" min={1} max={100} value={reps} onChange={(e) => setReps(parseInt(e.target.value) || 1)} disabled={isSubmitting} className="input" />
          </div>
          <div>
            <label htmlFor="edit-weight" className="block text-xs font-medium text-text-secondary mb-1.5">Weight (kg)</label>
            <input id="edit-weight" type="text" placeholder="BW" value={weight} onChange={(e) => setWeight(e.target.value)} disabled={isSubmitting} className="input" />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button type="submit" className="btn btn-primary flex-1" disabled={isSubmitting}>
            {isSubmitting ? 'Updating...' : 'Update Exercise'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </button>
        </div>

        {onDelete && (
          <div className="pt-2 border-t border-border">
            {confirmDelete ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-danger">Delete this exercise?</span>
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  onClick={() => { onDelete(exercise.id); onCancel(); }}
                  disabled={isSubmitting}
                >
                  Confirm Delete
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => setConfirmDelete(false)}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="btn btn-ghost btn-sm text-danger hover:bg-danger/10"
                onClick={() => setConfirmDelete(true)}
                disabled={isSubmitting}
              >
                <Trash2 size={14} />
                Delete Exercise
              </button>
            )}
          </div>
        )}
      </form>
    </Modal>
  );
}
