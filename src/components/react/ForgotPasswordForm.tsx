import React, { useState } from 'react';
import { api } from '../../lib/api';
import { showToast } from './Toast';

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ message: string; reset_token?: string } | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!email || !email.includes('@')) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.forgotPassword(email);
      setResult(res);
      showToast('Password reset instructions generated.', 'success');
    } catch (err: any) {
      const msg = err.message || 'Failed to process password reset request.';
      setErrorMessage(msg);
      showToast(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl backdrop-blur-sm">
      <div className="mb-6">
        <a href="/login" className="text-xs font-semibold text-sky-600 dark:text-sky-400 hover:underline inline-flex items-center gap-1 mb-2">
          ← Back to Sign In
        </a>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          Reset Your Password
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Enter the email associated with your account, and we will issue a secure reset token.
        </p>
      </div>

      {result ? (
        <div className="space-y-4 animate-fade-in">
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-800 dark:text-emerald-300">
            <div className="font-bold flex items-center gap-1.5 mb-1">
              <span>✓</span> Instructions Generated
            </div>
            <p>{result.message}</p>
          </div>

          {result.reset_token && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-2">
              <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                Generated Security Reset Token:
              </div>
              <div className="p-2 rounded bg-white dark:bg-slate-900 font-mono text-xs text-sky-600 dark:text-sky-400 select-all break-all border border-slate-200 dark:border-slate-800">
                {result.reset_token}
              </div>
              <a
                href={`/reset-password?token=${encodeURIComponent(result.reset_token)}`}
                className="block text-center py-2 px-3 rounded-lg text-xs font-bold bg-sky-500 hover:bg-sky-400 text-white shadow transition-all"
              >
                Proceed to Set New Password →
              </a>
            </div>
          )}

          <div className="text-center pt-2">
            <a href="/login" className="text-xs font-bold text-slate-600 dark:text-slate-400 hover:underline">
              Return to Login
            </a>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2">
              <span>⚠️</span>
              <span>{errorMessage}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5" htmlFor="forgot-email">
              Registered Email Address
            </label>
            <input
              id="forgot-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. student@uop.edu.pk"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-lg shadow-sky-500/25 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Generating Token...</span>
              </>
            ) : (
              <span>Request Password Reset →</span>
            )}
          </button>
        </form>
      )}
    </div>
  );
}
