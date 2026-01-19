/**
 * Form component for creating a new exercise.
 */

import { useState, FormEvent } from 'react';
import type { CreateExerciseRequest } from '../types/exercise';

interface CreateExerciseFormProps {
  onSubmit: (data: CreateExerciseRequest) => Promise<void>;
}

export function CreateExerciseForm({ onSubmit }: CreateExerciseFormProps) {
  const [name, setName] = useState('');
  const [sets, setSets] = useState(3);
  const [reps, setReps] = useState(10);
  const [weight, setWeight] = useState('');
  const [workoutDay, setWorkoutDay] = useState('A');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name.trim()) {
      setError('Exercise name is required!');
      return;
    }

    // Parse weight
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

      const weightDisplay = weightValue ? `${weightValue} kg` : 'Bodyweight';
      setSuccess(`Created exercise: ${name} (${sets} sets × ${reps} reps, ${weightDisplay})`);

      // Reset form
      setName('');
      setSets(3);
      setReps(10);
      setWeight('');
      setWorkoutDay('A');
    } catch (err) {
      setError(`Failed to create exercise: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="form-section">
      <h2>Add New Exercise</h2>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="create-name">Exercise Name *</label>
            <input
              id="create-name"
              type="text"
              placeholder="e.g., Bench Press"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="create-sets">Sets *</label>
            <input
              id="create-sets"
              type="number"
              min={1}
              max={20}
              value={sets}
              onChange={(e) => setSets(parseInt(e.target.value) || 1)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="create-reps">Reps *</label>
            <input
              id="create-reps"
              type="number"
              min={1}
              max={100}
              value={reps}
              onChange={(e) => setReps(parseInt(e.target.value) || 1)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="create-weight">Weight (kg)</label>
            <input
              id="create-weight"
              type="text"
              placeholder="Leave empty for bodyweight"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="create-workout-day">Workout Day *</label>
            <select
              id="create-workout-day"
              value={workoutDay}
              onChange={(e) => setWorkoutDay(e.target.value)}
              disabled={isSubmitting}
            >
              <option value="None">Daily (Every Day)</option>
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

        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Creating...' : 'Create Exercise'}
        </button>
      </form>
    </div>
  );
}

