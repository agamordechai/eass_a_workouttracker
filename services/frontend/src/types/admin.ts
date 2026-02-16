/**
 * Admin dashboard type definitions.
 */

export interface AdminUser {
  id: number;
  email: string;
  name: string;
  picture_url: string | null;
  role: string;
  disabled: boolean;
  created_at: string;
  exercise_count: number;
}

export interface AdminStats {
  total_users: number;
  total_exercises: number;
  recent_signups_7d: number;
  active_users_7d: number;
}
