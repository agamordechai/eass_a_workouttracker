import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AnalysisReport } from './AnalysisReport';

// Mock the API client
vi.mock('../../api/client', () => ({
    getProgressAnalysis: vi.fn(),
}));

// Mock the ProgressRing component since it's not relevant to these tests
vi.mock('../ui/ProgressRing', () => ({
    ProgressRing: ({ value }: { value: number }) => <div data-testid="progress-ring">{value}</div>,
}));

describe('AnalysisReport', () => {
    beforeEach(() => {
        sessionStorage.clear();
    });

    it('renders the analyze button by default', () => {
        render(<AnalysisReport />);
        expect(screen.getByText('Analyze My Routine')).toBeInTheDocument();
    });

    it('restores analysis from sessionStorage', () => {
        const savedAnalysis = {
            summary: 'Your routine is well-balanced.',
            strengths: ['Good upper body volume'],
            areas_to_improve: ['Add more leg work'],
            recommendations: ['Include lunges'],
            muscle_balance_score: 75,
        };
        sessionStorage.setItem('coach_analysis', JSON.stringify(savedAnalysis));

        render(<AnalysisReport />);
        expect(screen.getByText('Your routine is well-balanced.')).toBeInTheDocument();
        expect(screen.getByText('Good upper body volume')).toBeInTheDocument();
        expect(screen.getByText('Add more leg work')).toBeInTheDocument();
        expect(screen.getByText('Include lunges')).toBeInTheDocument();
        expect(screen.getByTestId('progress-ring')).toHaveTextContent('75');
    });

    it('shows the landing state when no saved analysis exists', () => {
        render(<AnalysisReport />);
        expect(screen.getByText(/AI-powered analysis/)).toBeInTheDocument();
        expect(screen.getByText('Analyze My Routine')).toBeInTheDocument();
    });
});
