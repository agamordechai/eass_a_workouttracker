/**
 * TypeScript types for AI Coach service
 */

export type MuscleGroup =
  | 'chest'
  | 'back'
  | 'shoulders'
  | 'biceps'
  | 'triceps'
  | 'legs'
  | 'core'
  | 'full_body'
  | 'upper_lower'
  | 'push_pull_legs';

export interface ChatRequest {
  message: string;
  include_workout_context: boolean;
}

export interface ChatResponse {
  response: string;
  context_used: boolean;
}

export interface RecommendationRequest {
  focus_area?: MuscleGroup;
  custom_focus_area?: string;
  equipment_available?: string[];
  session_duration_minutes?: number;
}

export interface ExerciseRecommendation {
  name: string;
  sets: number;
  reps: string;
  weight_suggestion?: string;
  notes?: string;
  muscle_group: MuscleGroup;
  workout_day: string;
}

export interface WorkoutRecommendation {
  title: string;
  description: string;
  exercises: ExerciseRecommendation[];
  estimated_duration_minutes: number;
  difficulty: string;
  tips: string[];
  split_type: string;
}

export interface ProgressAnalysis {
  summary: string;
  strengths: string[];
  areas_to_improve: string[];
  recommendations: string[];
  muscle_balance_score?: number;
}

export interface AICoachHealthResponse {
  status: string;
  service: string;
  ai_model: string;
  workout_api_connected: boolean;
  redis_connected: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

