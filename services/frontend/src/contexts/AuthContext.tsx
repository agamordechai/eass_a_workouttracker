/**
 * Authentication context providing Google Sign-In state management.
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { googleLogin, loginEmail, registerEmail, getCurrentUser, updateProfile as updateProfileApi, deleteAccount as deleteAccountApi } from '../api/client';
import type { User } from '../types/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (googleIdToken: string) => Promise<void>;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: { name?: string }) => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  // On mount, check for existing tokens and validate
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => {
        // Token is invalid or expired, clear it
        logout();
      })
      .finally(() => setLoading(false));
  }, [logout]);

  const storeTokensAndLoadUser = useCallback(async (tokens: { access_token: string; refresh_token: string | null }) => {
    localStorage.setItem('access_token', tokens.access_token);
    if (tokens.refresh_token) {
      localStorage.setItem('refresh_token', tokens.refresh_token);
    }
    const currentUser = await getCurrentUser();
    setUser(currentUser);
  }, []);

  const login = useCallback(async (googleIdToken: string) => {
    const tokens = await googleLogin(googleIdToken);
    await storeTokensAndLoadUser(tokens);
  }, [storeTokensAndLoadUser]);

  const loginWithEmail = useCallback(async (email: string, password: string) => {
    const tokens = await loginEmail(email, password);
    await storeTokensAndLoadUser(tokens);
  }, [storeTokensAndLoadUser]);

  const register = useCallback(async (email: string, name: string, password: string) => {
    const tokens = await registerEmail(email, name, password);
    await storeTokensAndLoadUser(tokens);
  }, [storeTokensAndLoadUser]);

  const updateProfile = useCallback(async (data: { name?: string }) => {
    const updatedUser = await updateProfileApi(data);
    setUser(updatedUser);
  }, []);

  const deleteAccount = useCallback(async () => {
    await deleteAccountApi();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: user !== null,
        login,
        loginWithEmail,
        register,
        logout,
        updateProfile,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
