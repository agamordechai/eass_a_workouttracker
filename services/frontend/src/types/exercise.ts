/**
 * Exercise type definitions matching the FastAPI backend models.
 */

export interface Exercise {
  id: number;
  name: string;
  sets: number;
  reps: number;
  weight: number | null;
}

export interface CreateExerciseRequest {
  name: string;
  sets: number;
  reps: number;
  weight?: number | null;
}

export interface UpdateExerciseRequest {
  name?: string;
  sets?: number;
  reps?: number;
  weight?: number | null;
}

export type FilterType = 'All' | 'Weighted Only' | 'Bodyweight Only';

