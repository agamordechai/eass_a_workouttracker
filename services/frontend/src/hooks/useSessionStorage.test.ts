import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSessionStorage } from './useSessionStorage';

describe('useSessionStorage', () => {
    beforeEach(() => {
        sessionStorage.clear();
    });

    it('returns the initial value when sessionStorage is empty', () => {
        const { result } = renderHook(() => useSessionStorage('test-key', 'hello'));
        expect(result.current[0]).toBe('hello');
    });

    it('reads an existing value from sessionStorage', () => {
        sessionStorage.setItem('test-key', JSON.stringify('saved'));
        const { result } = renderHook(() => useSessionStorage('test-key', 'default'));
        expect(result.current[0]).toBe('saved');
    });

    it('writes updated values to sessionStorage', () => {
        const { result } = renderHook(() => useSessionStorage('test-key', 'initial'));

        act(() => {
            result.current[1]('updated');
        });

        expect(result.current[0]).toBe('updated');
        expect(JSON.parse(sessionStorage.getItem('test-key')!)).toBe('updated');
    });

    it('supports functional updates', () => {
        const { result } = renderHook(() => useSessionStorage('counter', 0));

        act(() => {
            result.current[1]((prev) => prev + 1);
        });

        expect(result.current[0]).toBe(1);
        expect(JSON.parse(sessionStorage.getItem('counter')!)).toBe(1);
    });

    it('handles objects and arrays', () => {
        const initial = [{ role: 'user', content: 'hi' }];
        const { result } = renderHook(() => useSessionStorage('messages', initial));

        act(() => {
            result.current[1]((prev) => [...prev, { role: 'assistant', content: 'hello' }]);
        });

        expect(result.current[0]).toHaveLength(2);
        expect(result.current[0][1].content).toBe('hello');
    });

    it('handles null initial values', () => {
        const { result } = renderHook(() => useSessionStorage<string | null>('nullable', null));
        expect(result.current[0]).toBeNull();

        act(() => {
            result.current[1]('non-null');
        });

        expect(result.current[0]).toBe('non-null');
    });

    it('falls back to initial value when sessionStorage contains invalid JSON', () => {
        sessionStorage.setItem('bad-json', '{invalid');
        const { result } = renderHook(() => useSessionStorage('bad-json', 'fallback'));
        expect(result.current[0]).toBe('fallback');
    });

    it('persists across re-renders with the same key', () => {
        const { result, rerender } = renderHook(() => useSessionStorage('persist-key', 'init'));

        act(() => {
            result.current[1]('changed');
        });

        rerender();
        expect(result.current[0]).toBe('changed');
    });
});
