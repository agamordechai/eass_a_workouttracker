/**
 * Exercise type definitions matching the FastAPI backend models.
 */

export interface Exercise {
  id: number;
  name: string;
  sets: number;
  reps: number;
  weight: number | null;
  workout_day: string;
}

export interface CreateExerciseRequest {
  name: string;
  sets: number;
  reps: number;
  weight?: number | null;
  workout_day?: string;
}

export interface UpdateExerciseRequest {
  name?: string;
  sets?: number;
  reps?: number;
  weight?: number | null;
  workout_day?: string;
}

export type FilterType = 'All' | 'Weighted Only' | 'Bodyweight Only';

