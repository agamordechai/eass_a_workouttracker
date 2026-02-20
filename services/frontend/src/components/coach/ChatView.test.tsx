import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatView } from './ChatView';

// Mock the API client
vi.mock('../../api/client', () => ({
    chatWithCoach: vi.fn().mockResolvedValue({ response: 'Mocked reply', context_used: true }),
}));

describe('ChatView', () => {
    beforeEach(() => {
        sessionStorage.clear();
    });

    it('renders the default welcome message', () => {
        render(<ChatView />);
        expect(screen.getByText(/I'm your AI fitness coach/)).toBeInTheDocument();
    });

    it('restores chat history from sessionStorage', () => {
        const savedMessages = [
            { role: 'assistant', content: 'Hello!' },
            { role: 'user', content: 'How do I deadlift?' },
            { role: 'assistant', content: 'Keep your back straight.' },
        ];
        sessionStorage.setItem('coach_chat_messages', JSON.stringify(savedMessages));

        render(<ChatView />);
        expect(screen.getByText('How do I deadlift?')).toBeInTheDocument();
        expect(screen.getByText('Keep your back straight.')).toBeInTheDocument();
    });

    it('renders the New Chat button', () => {
        render(<ChatView />);
        expect(screen.getByText('New Chat')).toBeInTheDocument();
    });

    it('resets chat to default when New Chat is clicked', () => {
        const savedMessages = [
            { role: 'assistant', content: 'Hello!' },
            { role: 'user', content: 'Test message' },
        ];
        sessionStorage.setItem('coach_chat_messages', JSON.stringify(savedMessages));

        render(<ChatView />);
        expect(screen.getByText('Test message')).toBeInTheDocument();

        fireEvent.click(screen.getByText('New Chat'));
        expect(screen.queryByText('Test message')).not.toBeInTheDocument();
        expect(screen.getByText(/I'm your AI fitness coach/)).toBeInTheDocument();
    });

    it('saves messages to sessionStorage after sending', async () => {
        render(<ChatView />);

        const textarea = screen.getByPlaceholderText('Ask your AI coach anything...');
        fireEvent.change(textarea, { target: { value: 'Hello coach' } });
        fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

        await waitFor(() => {
            const stored = JSON.parse(sessionStorage.getItem('coach_chat_messages')!);
            expect(stored.length).toBeGreaterThan(1);
            expect(stored.some((m: any) => m.content === 'Hello coach')).toBe(true);
        });
    });
});
