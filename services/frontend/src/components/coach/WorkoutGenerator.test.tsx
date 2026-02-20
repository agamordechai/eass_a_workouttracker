import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkoutGenerator } from './WorkoutGenerator';

// Mock the API client
vi.mock('../../api/client', () => ({
    getWorkoutRecommendation: vi.fn(),
    appendExercisesToRoutine: vi.fn(),
}));

// Mock the constants
vi.mock('../../lib/constants', () => ({
    MUSCLE_GROUPS: [
        { value: 'full_body', label: 'Full Body' },
        { value: 'chest', label: 'Chest' },
    ],
    EQUIPMENT_OPTIONS: ['barbell', 'dumbbells', 'cables', 'bodyweight'],
    ALL_DAYS: ['A', 'B', 'C'],
    getDayColor: () => ({ bg: 'bg-gray-100', text: 'text-gray-800', border: 'border-gray-200' }),
}));

describe('WorkoutGenerator', () => {
    beforeEach(() => {
        sessionStorage.clear();
    });

    it('renders the generate form by default', () => {
        render(<WorkoutGenerator />);
        expect(screen.getByText('Generate Routine')).toBeInTheDocument();
    });

    it('renders duration slider with 5 min to 2 hrs range', () => {
        render(<WorkoutGenerator />);
        expect(screen.getByText('5 min')).toBeInTheDocument();
        expect(screen.getByText('2 hrs')).toBeInTheDocument();

        const slider = screen.getByRole('slider');
        expect(slider).toHaveAttribute('min', '5');
        expect(slider).toHaveAttribute('max', '120');
    });

    it('restores recommendation from sessionStorage', () => {
        const savedRecommendation = {
            title: 'Upper Body Blast',
            description: 'A killer upper body workout',
            exercises: [
                { name: 'Bench Press', sets: 4, reps: '8-10', muscle_group: 'chest', workout_day: 'A' },
            ],
            estimated_duration_minutes: 45,
            difficulty: 'intermediate',
            tips: ['Warm up properly'],
            split_type: 'upper/lower',
        };
        sessionStorage.setItem('coach_workout_recommendation', JSON.stringify(savedRecommendation));

        render(<WorkoutGenerator />);
        expect(screen.getByText('Upper Body Blast')).toBeInTheDocument();
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
        expect(screen.getByText('Warm up properly')).toBeInTheDocument();
    });

    it('shows the generate form when no saved recommendation exists', () => {
        render(<WorkoutGenerator />);
        expect(screen.getByText('Focus Area')).toBeInTheDocument();
        expect(screen.getByText('Generate Routine')).toBeInTheDocument();
    });
});
