import { useState, FormEvent } from 'react';
import type { CreateExerciseRequest } from '../types/exercise';

interface CreateExerciseModalProps {
  onSubmit: (data: CreateExerciseRequest) => Promise<void>;
  onClose: () => void;
}

export function CreateExerciseModal({ onSubmit, onClose }: CreateExerciseModalProps) {
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
      onClose();
    } catch (err) {
      setError(`Failed to create exercise: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div className="card w-full max-w-lg animate-fadeIn" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-text-primary">Create Exercise</h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors p-1">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded px-3 py-2 mb-3">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="create-name" className="block text-xs font-medium text-text-secondary mb-1">Exercise Name *</label>
            <input id="create-name" type="text" placeholder="e.g., Bench Press" value={name} onChange={(e) => setName(e.target.value)} disabled={isSubmitting} className="input" autoFocus />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label htmlFor="create-sets" className="block text-xs font-medium text-text-secondary mb-1">Sets *</label>
              <input id="create-sets" type="number" min={1} max={20} value={sets} onChange={(e) => setSets(parseInt(e.target.value) || 1)} disabled={isSubmitting} className="input" />
            </div>
            <div>
              <label htmlFor="create-reps" className="block text-xs font-medium text-text-secondary mb-1">Reps *</label>
              <input id="create-reps" type="number" min={1} max={100} value={reps} onChange={(e) => setReps(parseInt(e.target.value) || 1)} disabled={isSubmitting} className="input" />
            </div>
            <div>
              <label htmlFor="create-weight" className="block text-xs font-medium text-text-secondary mb-1">Weight (kg)</label>
              <input id="create-weight" type="text" placeholder="Bodyweight" value={weight} onChange={(e) => setWeight(e.target.value)} disabled={isSubmitting} className="input" />
            </div>
            <div>
              <label htmlFor="create-workout-day" className="block text-xs font-medium text-text-secondary mb-1">Day *</label>
              <select id="create-workout-day" value={workoutDay} onChange={(e) => setWorkoutDay(e.target.value)} disabled={isSubmitting} className="input">
                <option value="None">Daily</option>
                <option value="A">Day A</option>
                <option value="B">Day B</option>
                <option value="C">Day C</option>
                <option value="D">Day D</option>
                <option value="E">Day E</option>
                <option value="F">Day F</option>
                <option value="G">Day G</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-1">
            <button type="submit" className="btn btn-primary flex-1" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Exercise'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
