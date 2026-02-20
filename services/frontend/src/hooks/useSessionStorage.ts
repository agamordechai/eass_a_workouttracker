import { useState, useEffect, useCallback } from 'react';

/**
 * A drop-in replacement for useState that persists the value in sessionStorage.
 * Data survives navigation within the tab but is cleared when the tab closes.
 */
export function useSessionStorage<T>(
    key: string,
    initialValue: T,
): [T, React.Dispatch<React.SetStateAction<T>>] {
    const [storedValue, setStoredValue] = useState<T>(() => {
        try {
            const item = sessionStorage.getItem(key);
            return item ? (JSON.parse(item) as T) : initialValue;
        } catch {
            return initialValue;
        }
    });

    useEffect(() => {
        try {
            sessionStorage.setItem(key, JSON.stringify(storedValue));
        } catch {
            // sessionStorage full or unavailable — silently ignore
        }
    }, [key, storedValue]);

    const setValue: React.Dispatch<React.SetStateAction<T>> = useCallback(
        (value) => {
            setStoredValue((prev) => {
                const next = value instanceof Function ? value(prev) : value;
                return next;
            });
        },
        [],
    );

    return [storedValue, setValue];
}
