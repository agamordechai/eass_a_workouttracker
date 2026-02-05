/**
 * API client for the Workout Tracker backend.
 * Mirrors the functionality of the Python client.py
 */

import axios, { AxiosInstance } from 'axios';
import type { Exercise, CreateExerciseRequest, UpdateExerciseRequest, PaginatedExerciseResponse } from '../types/exercise';
import type {
  ChatRequest,
  ChatResponse,
  RecommendationRequest,
  WorkoutRecommendation,
  ProgressAnalysis,
  AICoachHealthResponse,
} from '../types/aiCoach';

// In development, Vite proxies /api to localhost:8000
// In production, configure API_BASE_URL environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const AI_COACH_BASE_URL = import.meta.env.VITE_AI_COACH_BASE_URL || '/ai-coach';
const TRACE_ID = 'ui-react';

const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'X-Trace-Id': TRACE_ID,
  },
});

const aiCoachClient: AxiosInstance = axios.create({
  baseURL: AI_COACH_BASE_URL,
  timeout: 60000, // Longer timeout for AI responses
  headers: {
    'Content-Type': 'application/json',
    'X-Trace-Id': TRACE_ID,
  },
});

export interface ExerciseListParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}

/**
 * Fetch exercises with optional pagination and sorting.
 */
export async function listExercises(params?: ExerciseListParams): Promise<PaginatedExerciseResponse> {
  const response = await client.get<PaginatedExerciseResponse>('/exercises', { params });
  return response.data;
}

/**
 * Download all exercises as a CSV file.
 */
export async function exportExercisesCSV(): Promise<void> {
  const response = await client.get('/exercises', {
    params: { format: 'csv', page_size: 200 },
    responseType: 'blob',
  });
  const url = URL.createObjectURL(response.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'exercises.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Fetch a specific exercise by ID.
 */
export async function getExercise(exerciseId: number): Promise<Exercise> {
  const response = await client.get<Exercise>(`/exercises/${exerciseId}`);
  return response.data;
}

/**
 * Create a new exercise in the tracker.
 */
export async function createExercise(data: CreateExerciseRequest): Promise<Exercise> {
  const response = await client.post<Exercise>('/exercises', data);
  return response.data;
}

/**
 * Update an existing exercise (partial update).
 */
export async function updateExercise(
  exerciseId: number,
  data: UpdateExerciseRequest
): Promise<Exercise> {
  const response = await client.patch<Exercise>(`/exercises/${exerciseId}`, data);
  return response.data;
}

/**
 * Delete an exercise from the tracker.
 */
export async function deleteExercise(exerciseId: number): Promise<void> {
  await client.delete(`/exercises/${exerciseId}`);
}

// ============ AI Coach API ============

/**
 * Check AI Coach service health.
 */
export async function getAICoachHealth(): Promise<AICoachHealthResponse> {
  const response = await aiCoachClient.get<AICoachHealthResponse>('/health');
  return response.data;
}

/**
 * Chat with the AI Coach.
 */
export async function chatWithCoach(
  message: string,
  includeWorkoutContext: boolean = true
): Promise<ChatResponse> {
  const request: ChatRequest = {
    message,
    include_workout_context: includeWorkoutContext,
  };
  const response = await aiCoachClient.post<ChatResponse>('/chat', request);
  return response.data;
}

/**
 * Get workout recommendations from AI Coach.
 */
export async function getWorkoutRecommendation(
  request: RecommendationRequest = {}
): Promise<WorkoutRecommendation> {
  const response = await aiCoachClient.post<WorkoutRecommendation>('/recommend', request);
  return response.data;
}

/**
 * Get progress analysis from AI Coach.
 */
export async function getProgressAnalysis(): Promise<ProgressAnalysis> {
  const response = await aiCoachClient.get<ProgressAnalysis>('/analyze');
  return response.data;
}

export default client;

