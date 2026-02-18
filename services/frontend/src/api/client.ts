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
import type { User, AuthTokens } from '../types/auth';
import type { AdminUser, AdminStats } from '../types/admin';

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

// ---------- Auth interceptors ----------

function attachAuthHeader(config: any) {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers = config.headers || {};
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
}

client.interceptors.request.use(attachAuthHeader);
aiCoachClient.interceptors.request.use(attachAuthHeader);

// Attach user-provided Anthropic key for AI Coach requests
aiCoachClient.interceptors.request.use((config) => {
  const key = localStorage.getItem('anthropic_api_key');
  if (key) {
    config.headers = config.headers || {};
    config.headers['X-Anthropic-Key'] = key;
  }
  return config;
});

// Response interceptor: attempt token refresh on 401
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post<AuthTokens>(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken },
            { headers: { 'Content-Type': 'application/json' } },
          );
          localStorage.setItem('access_token', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
          }
          originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
          return client(originalRequest);
        } catch {
          // Refresh failed — clear tokens and reload
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.reload();
        }
      }
    }
    return Promise.reject(error);
  },
);

// ---------- Auth API functions ----------

export async function googleLogin(idToken: string): Promise<AuthTokens> {
  const response = await client.post<AuthTokens>('/auth/google', { id_token: idToken });
  return response.data;
}

export async function registerEmail(
  email: string,
  name: string,
  password: string,
): Promise<AuthTokens> {
  const response = await client.post<AuthTokens>('/auth/register', { email, name, password });
  return response.data;
}

export async function loginEmail(email: string, password: string): Promise<AuthTokens> {
  const response = await client.post<AuthTokens>('/auth/login', { email, password });
  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await client.get<User>('/auth/me');
  return response.data;
}

export async function updateProfile(data: { name?: string }): Promise<User> {
  const response = await client.patch<User>('/auth/me', data);
  return response.data;
}

export async function deleteAccount(): Promise<void> {
  await client.delete('/auth/me');
}

// ---------- Exercise API functions ----------

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

/**
 * Delete all exercises for the current user.
 */
export async function clearExercises(): Promise<{ deleted: number }> {
  const response = await client.delete<{ deleted: number }>('/exercises');
  return response.data;
}

/**
 * Seed default sample exercises for the current user.
 */
export async function seedExercises(split: 'ppl' | 'ab' | 'fullbody' = 'ppl'): Promise<{ seeded: number }> {
  const response = await client.post<{ seeded: number }>(`/exercises/seed?split=${split}`);
  return response.data;
}

// ============ Admin API ============

export async function getAdminUsers(): Promise<AdminUser[]> {
  const response = await client.get<AdminUser[]>('/admin/users');
  return response.data;
}

export async function getAdminStats(): Promise<AdminStats> {
  const response = await client.get<AdminStats>('/admin/stats');
  return response.data;
}

export async function updateAdminUser(
  userId: number,
  data: { role?: string; disabled?: boolean },
): Promise<AdminUser> {
  const response = await client.patch<AdminUser>(`/admin/users/${userId}`, data);
  return response.data;
}

export async function deleteAdminUser(userId: number): Promise<void> {
  await client.delete(`/admin/users/${userId}`);
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

/**
 * Parse a reps string like "8-12" or "10" to an integer (lower bound).
 */
function parseReps(reps: string): number {
  const match = reps.match(/\d+/);
  return match ? parseInt(match[0], 10) : 10;
}

/**
 * Parse a weight suggestion string like "60kg" or "20 lbs" to a float (kg), or null.
 */
function parseWeight(weightSuggestion: string | undefined): number | null {
  if (!weightSuggestion) return null;
  const lower = weightSuggestion.toLowerCase();
  if (lower.includes('bodyweight') || lower.includes('bw') || lower === '-') return null;
  const match = weightSuggestion.match(/[\d.]+/);
  if (!match) return null;
  const val = parseFloat(match[0]);
  // Convert lbs to kg if needed
  if (lower.includes('lb') || lower.includes('pound')) return Math.round(val * 0.453592 * 10) / 10;
  return val;
}

export interface ExerciseToImport {
  name: string;
  sets: number;
  reps: string;
  weight_suggestion?: string;
  workout_day: string;
}

/**
 * Append selected exercises to the user's routine (no data is deleted).
 */
export async function appendExercisesToRoutine(exercises: ExerciseToImport[]): Promise<void> {
  for (const ex of exercises) {
    await createExercise({
      name: ex.name,
      sets: ex.sets,
      reps: parseReps(ex.reps),
      weight: parseWeight(ex.weight_suggestion),
      workout_day: ex.workout_day,
    });
  }
}

export default client;
