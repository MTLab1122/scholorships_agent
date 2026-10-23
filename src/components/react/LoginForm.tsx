import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { auth } from '../../lib/auth';
import { showToast } from './Toast';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [rateLimitTimer, setRateLimitTimer] = useState<number | null>(null);

  useEffect(() => {
    // If already authenticated, redirect to appropriate dashboard
    const user = auth.getUser();
    if (user && auth.isAuthenticated()) {
      const params = new URLSearchParams(window.location.search);
      const redirect = params.get('redirect');
      if (redirect) {
        window.location.href = redirect;
      } else if (user.role === 'admin') {
        window.location.href = '/admin/dashboard';
      } else {
        window.location.href = '/student/dashboard';
      }
    }
  }, []);

  // Handle rate limit countdown
  useEffect(() => {
    if (rateLimitTimer === null) return;
    if (rateLimitTimer <= 0) {
      setRateLimitTimer(null);
      setErrorMessage('');
      return;
    }
    const interval = setInterval(() => {
      setRateLimitTimer((prev) => (prev !== null && prev > 0 ? prev - 1 : null));
    }, 1000);
    return () => clearInterval(interval);
  }, [rateLimitTimer]);

  const handleQuickFill = (role: 'admin' | 'student') => {
    if (role === 'admin') {
      setEmail('admin@opportunity.edu.pk');
      setPassword('AdminPassword123!');
    } else {
      setEmail('student@uop.edu.pk');
      setPassword('StudentPassword123!');
    }
    setErrorMessage('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!email || !email.includes('@')) {
      setErrorMessage('Please enter a valid academic or personal email address.');
      return;
    }
    if (!password || password.length < 6) {
      setErrorMessage('Password must be at least 6 characters.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.login({ email, password });
      auth.setSession(res.token, res.user);
      showToast('Logged in successfully! Redirecting...', 'success');

      const params = new URLSearchParams(window.location.search);
      const redirect = params.get('redirect');
      setTimeout(() => {
        if (redirect) {
          window.location.href = redirect;
        } else if (res.user.role === 'admin') {
          window.location.href = '/admin/dashboard';
        } else {
          window.location.href = '/student/dashboard';
        }
      }, 500);
    } catch (err: any) {
      const msg = err.message || 'Login failed. Please check your credentials.';
      if (msg.includes('429') || msg.toLowerCase().includes('rate limit')) {
        setRateLimitTimer(60);
        setErrorMessage('Rate limit reached on authentication. Please wait 60 seconds before retrying.');
        showToast('Rate limit exceeded. Please wait a moment.', 'warning');
      } else {
        setErrorMessage(msg);
        showToast(msg, 'error');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Demo Credentials Helper Pill */}
      <div className="mb-6 p-3 rounded-xl bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800/60 text-xs">
        <div className="font-semibold text-sky-800 dark:text-sky-300 flex items-center justify-between mb-2">
          <span>⚡ Instant Evaluation Credentials:</span>
          <span className="text-[10px] text-sky-600 dark:text-sky-400 font-mono">Pre-seeded</span>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleQuickFill('student')}
            className="flex-1 py-1.5 px-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-sky-100 dark:hover:bg-slate-700 text-sky-700 dark:text-sky-300 font-semibold border border-sky-200 dark:border-sky-700 transition-colors text-center"
          >
            🎓 Student Demo
          </button>
          <button
            type="button"
            onClick={() => handleQuickFill('admin')}
            className="flex-1 py-1.5 px-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-indigo-100 dark:hover:bg-slate-700 text-indigo-700 dark:text-indigo-300 font-semibold border border-indigo-200 dark:border-indigo-700 transition-colors text-center"
          >
            ⚡ Admin Demo
          </button>
        </div>
      </div>

      {/* Main Login Card */}
      <div className="bg-white dark:bg-slate-900 p-5 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl backdrop-blur-sm">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Sign In to SOI
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Access scholarships, personalized matches, Kanban tracking, and AI agents.
          </p>
        </div>

        {errorMessage && (
          <div
            role="alert"
            className="mb-5 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2 animate-fade-in"
          >
            <span className="text-base font-bold leading-none">⚠️</span>
            <div className="flex-1">
              {errorMessage}
              {rateLimitTimer !== null && (
                <div className="mt-1 font-mono font-bold text-rose-600 dark:text-rose-400">
                  Retry available in: {rateLimitTimer}s
                </div>
              )}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5" htmlFor="email-input">
              Academic or Personal Email
            </label>
            <input
              id="email-input"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. student@uop.edu.pk or user@example.com"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none transition-all"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300" htmlFor="password-input">
                Password
              </label>
              <a
                href="/forgot-password"
                className="text-[11px] font-semibold text-sky-600 dark:text-sky-400 hover:underline"
              >
                Forgot password?
              </a>
            </div>
            <div className="relative">
              <input
                id="password-input"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none transition-all pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs pt-1">
            <label className="flex items-center gap-2 cursor-pointer text-slate-600 dark:text-slate-400">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-slate-300 text-sky-600 focus:ring-sky-500"
              />
              <span>Remember this device (7 days)</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading || rateLimitTimer !== null}
            className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-lg shadow-sky-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Authenticating...</span>
              </>
            ) : (
              <span>Sign In →</span>
            )}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800 text-center text-xs text-slate-500 dark:text-slate-400">
          Don&apos;t have an account yet?{' '}
          <a href="/register" className="font-bold text-sky-600 dark:text-sky-400 hover:underline">
            Create an Account
          </a>
        </div>
      </div>

      {/* Legal Links */}
      <div className="mt-6 text-center text-[11px] text-slate-400 space-x-3">
        <a href="/privacy" className="hover:underline">Privacy Policy</a>
        <span>•</span>
        <a href="/terms" className="hover:underline">Terms of Service</a>
        <span>•</span>
        <a href="/verify-email" className="hover:underline">Verify Email</a>
      </div>
    </div>
  );
}
