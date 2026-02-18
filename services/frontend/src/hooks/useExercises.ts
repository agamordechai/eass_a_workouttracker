import { useState, useEffect, useCallback } from 'react';
import {
  listExercises,
  createExercise,
  updateExercise,
  deleteExercise,
  seedExercises,
} from '../api/client';
import type { Exercise, CreateExerciseRequest, UpdateExerciseRequest } from '../types/exercise';
import { useAuth } from '../contexts/AuthContext';

export function useExercises() {
  const { isAuthenticated } = useAuth();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExercises = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listExercises({ page_size: 200 });
      setExercises(data.items);
    } catch (err) {
      setError(
        `Failed to connect to the API. Is the backend running?\n${
          err instanceof Error ? err.message : 'Unknown error'
        }`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchExercises();
    const interval = setInterval(fetchExercises, 30000);
    return () => clearInterval(interval);
  }, [fetchExercises, isAuthenticated]);

  const handleCreate = async (data: CreateExerciseRequest) => {
    await createExercise(data);
    await fetchExercises();
  };

  const handleUpdate = async (exerciseId: number, data: UpdateExerciseRequest) => {
    await updateExercise(exerciseId, data);
    await fetchExercises();
  };

  const handleDelete = async (exerciseId: number) => {
    try {
      await deleteExercise(exerciseId);
      await fetchExercises();
    } catch (err) {
      alert(`Failed to delete: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleSeed = async (split: 'ppl' | 'ab' | 'fullbody') => {
    await seedExercises(split);
    await fetchExercises();
  };

  return {
    exercises,
    loading,
    error,
    fetchExercises,
    handleCreate,
    handleUpdate,
    handleDelete,
    handleSeed,
  };
}
