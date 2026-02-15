import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { validateEmail } from '../utils/emailValidation';
import axios from 'axios';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, config: any) => void;
        };
      };
    };
  }
}

export default function LoginPage() {
  const { login, loginWithEmail, register } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuggestion, setEmailSuggestion] = useState<string | null>(null);
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const googleButtonRef = useRef<HTMLDivElement>(null);
  const loginRef = useRef(login);

  // Keep the login function reference up to date
  useEffect(() => {
    loginRef.current = login;
  }, [login]);

  useEffect(() => {
    // Load Google Identity Services script with English locale
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client?hl=en';
    script.async = true;
    script.defer = true;

    const initializeGoogle = () => {
      if (window.google && googleButtonRef.current) {
        const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: async (response: { credential: string }) => {
            try {
              await loginRef.current(response.credential);
            } catch (err) {
              console.error('Google login failed:', err);
            }
          },
        });
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: 'outline',
          size: 'large',
          shape: 'rectangular',
          text: 'signin_with',
          width: 300,
          locale: 'en',
        });
      }
    };

    script.onload = initializeGoogle;
    document.body.appendChild(script);

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setEmailError(null);
    setEmailSuggestion(null);

    // Validate email format (especially for registration)
    if (isRegister) {
      const emailValidation = validateEmail(email);
      if (!emailValidation.isValid) {
        setEmailError(emailValidation.error || 'Invalid email');
        if (emailValidation.suggestion) {
          setEmailSuggestion(emailValidation.suggestion);
        }
        return;
      }
    }

    if (isRegister && password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setSubmitting(true);
    try {
      if (isRegister) {
        await register(email, name, password);
      } else {
        await loginWithEmail(email, password);
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="card space-y-5 p-6">
          {/* Logo + title */}
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-primary mx-auto mb-4 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-text-primary">Workout Tracker</h1>
            <p className="text-text-muted text-sm mt-1">
              {isRegister ? 'Create an account' : 'Sign in to track your workouts'}
            </p>
          </div>

          {/* Form */}
          <form className="space-y-3" onSubmit={handleEmailSubmit}>
            <div>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setEmailError(null);
                  setEmailSuggestion(null);
                }}
                required
                autoComplete="email"
                className={`input ${emailError ? 'border-danger' : ''}`}
              />
              {emailError && (
                <div className="mt-1">
                  <p className="text-danger text-xs">{emailError}</p>
                  {emailSuggestion && (
                    <button
                      type="button"
                      onClick={() => {
                        setEmail(emailSuggestion);
                        setEmailError(null);
                        setEmailSuggestion(null);
                      }}
                      className="text-xs text-primary hover:underline mt-1"
                    >
                      Use {emailSuggestion}
                    </button>
                  )}
                </div>
              )}
            </div>
            {isRegister && (
              <input type="text" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required autoComplete="name" className="input" />
            )}
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete={isRegister ? 'new-password' : 'current-password'} className="input" />
            {isRegister && (
              <input type="password" placeholder="Confirm Password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} autoComplete="new-password" className="input" />
            )}
            <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
              {submitting
                ? (isRegister ? 'Creating account...' : 'Signing in...')
                : (isRegister ? 'Create account' : 'Sign in')}
            </button>
          </form>

          {/* Toggle */}
          <p className="text-center text-sm text-text-muted">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              onClick={() => { setIsRegister(!isRegister); setError(null); setEmailError(null); setEmailSuggestion(null); setConfirmPassword(''); }}
              className="text-link hover:underline font-medium"
            >
              {isRegister ? 'Sign in' : 'Register'}
            </button>
          </p>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-border" />
            <span className="text-text-muted text-xs uppercase tracking-wider">or</span>
            <div className="flex-1 h-px bg-border" />
          </div>

          {/* Google */}
          <div className="flex justify-center">
            <div ref={googleButtonRef}></div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded px-3 py-2">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
