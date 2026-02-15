import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dumbbell } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { validateEmail } from '../../utils/emailValidation';
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

  useEffect(() => {
    loginRef.current = login;
  }, [login]);

  useEffect(() => {
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
    <div className="min-h-screen bg-background flex">
      {/* Left gradient panel (desktop only) */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-violet-600/20 via-purple-600/10 to-background items-center justify-center p-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-violet-500/30">
            <Dumbbell size={36} className="text-white" />
          </div>
          <h2 className="text-3xl font-bold text-text-primary mb-3">Workout Tracker</h2>
          <p className="text-text-secondary text-lg max-w-sm">
            Track your exercises, get AI coaching, and reach your fitness goals.
          </p>
        </motion.div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="w-full max-w-sm"
        >
          <div className="card space-y-6 p-6">
            {/* Logo + title (mobile) */}
            <div className="text-center lg:text-left">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mx-auto lg:mx-0 mb-4 shadow-lg shadow-violet-500/20">
                <Dumbbell size={24} className="text-white" />
              </div>
              <h1 className="text-xl font-bold text-text-primary">
                {isRegister ? 'Create an account' : 'Welcome back'}
              </h1>
              <p className="text-text-muted text-sm mt-1">
                {isRegister ? 'Start your fitness journey' : 'Sign in to track your workouts'}
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
                  className={`input ${emailError ? 'border-danger focus:border-danger' : ''}`}
                />
                <AnimatePresence>
                  {emailError && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-1"
                    >
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
                    </motion.div>
                  )}
                </AnimatePresence>
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
                className="text-primary hover:underline font-medium"
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
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="bg-danger/10 border border-danger/20 text-danger text-xs rounded-lg px-3 py-2"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
