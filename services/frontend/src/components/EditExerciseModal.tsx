/**
 * Modal component for editing an existing exercise.
 */

import { useState, FormEvent, useEffect } from 'react';
import type { Exercise, UpdateExerciseRequest } from '../types/exercise';

interface EditExerciseModalProps {
  exercise: Exercise;
  onSubmit: (exerciseId: number, data: UpdateExerciseRequest) => Promise<void>;
  onCancel: () => void;
}

export function EditExerciseModal({ exercise, onSubmit, onCancel }: EditExerciseModalProps) {
  const [name, setName] = useState(exercise.name);
  const [sets, setSets] = useState(exercise.sets);
  const [reps, setReps] = useState(exercise.reps);
  const [weight, setWeight] = useState(exercise.weight !== null ? String(exercise.weight) : '');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset form when exercise changes
  useEffect(() => {
    setName(exercise.name);
    setSets(exercise.sets);
    setReps(exercise.reps);
    setWeight(exercise.weight !== null ? String(exercise.weight) : '');
    setError('');
  }, [exercise]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

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
      await onSubmit(exercise.id, {
        name: name.trim(),
        sets,
        reps,
        weight: weightValue,
      });
      onCancel(); // Close modal on success
    } catch (err) {
      setError(`Failed to update exercise: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Update Exercise</h2>
        <p className="modal-info">
          Updating: <strong>{exercise.name}</strong> (ID: {exercise.id})
        </p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="edit-name">Exercise Name *</label>
            <input
              id="edit-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="edit-sets">Sets *</label>
              <input
                id="edit-sets"
                type="number"
                min={1}
                max={20}
                value={sets}
                onChange={(e) => setSets(parseInt(e.target.value) || 1)}
                disabled={isSubmitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="edit-reps">Reps *</label>
              <input
                id="edit-reps"
                type="number"
                min={1}
                max={100}
                value={reps}
                onChange={(e) => setReps(parseInt(e.target.value) || 1)}
                disabled={isSubmitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="edit-weight">Weight (kg)</label>
              <input
                id="edit-weight"
                type="text"
                placeholder="Leave empty for bodyweight"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className="modal-buttons">
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Updating...' : 'Update Exercise'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

