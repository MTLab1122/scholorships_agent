import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { showToast } from './Toast';

export default function VerifyEmailForm() {
  const [token, setToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const executeVerification = async (verifyToken: string) => {
    setIsLoading(true);
    setErrorMessage('');
    try {
      await api.verifyEmail(verifyToken);
      setIsSuccess(true);
      showToast('Email verified successfully!', 'success');
    } catch (err: any) {
      setErrorMessage(err.message || 'Verification token is invalid or has expired.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get('token');
    if (t) {
      setToken(t);
      executeVerification(t);
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (token) {
      executeVerification(token);
    }
  };

  if (isSuccess) {
    return (
      <div className="w-full max-w-md mx-auto bg-white dark:bg-slate-900 p-8 rounded-2xl border border-emerald-500/30 shadow-xl text-center animate-fade-in">
        <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-2xl mx-auto mb-4">
          ✓
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Email Confirmed!</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 mb-6">
          Your email address has been verified. You have full access to high-priority opportunities and notifications.
        </p>
        <a
          href="/student/dashboard"
          className="inline-block w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-sky-500 hover:bg-sky-400 text-white shadow-md transition-all"
        >
          Go to Student Dashboard →
        </a>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl backdrop-blur-sm">
      <div className="mb-6 text-center">
        <div className="w-12 h-12 rounded-xl bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 flex items-center justify-center text-2xl mx-auto mb-3">
          ✉️
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          Verify Your Email
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Paste the verification token provided at registration or received in your dispatch email.
        </p>
      </div>

      {errorMessage && (
        <div
          role="alert"
          className="mb-5 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2"
        >
          <span>⚠️</span>
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1" htmlFor="token-text">
            Email Verification Token
          </label>
          <input
            id="token-text"
            type="text"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste your 32-character token"
            className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white font-mono text-xs focus:ring-2 focus:ring-sky-500 outline-none"
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
              <span>Confirming Token...</span>
            </>
          ) : (
            <span>Verify Email Address →</span>
          )}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-slate-500">
        <a href="/login" className="hover:underline">Back to Login</a>
      </div>
    </div>
  );
}
