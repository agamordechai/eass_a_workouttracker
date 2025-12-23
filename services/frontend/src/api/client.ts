/**
 * API client for the Workout Tracker backend.
 * Mirrors the functionality of the Python client.py
 */

import axios, { AxiosInstance } from 'axios';
import type { Exercise, CreateExerciseRequest, UpdateExerciseRequest } from '../types/exercise';

// In development, Vite proxies /api to localhost:8000
// In production, configure API_BASE_URL environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const TRACE_ID = 'ui-react';

const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'X-Trace-Id': TRACE_ID,
  },
});

/**
 * Fetch all exercises from the API.
 */
export async function listExercises(): Promise<Exercise[]> {
  const response = await client.get<Exercise[]>('/exercises');
  return response.data;
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

export default client;

