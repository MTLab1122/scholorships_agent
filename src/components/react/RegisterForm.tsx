import React, { useState } from 'react';
import { api } from '../../lib/api';
import { auth } from '../../lib/auth';
import { showToast } from './Toast';

export default function RegisterForm() {
  const [role, setRole] = useState<'student' | 'admin'>('student');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Student specific details
  const [university, setUniversity] = useState('University of Peshawar');
  const [degreeLevel, setDegreeLevel] = useState('Undergraduate');
  const [discipline, setDiscipline] = useState('Computer Science');
  const [currentSemester, setCurrentSemester] = useState(4);
  const [cgpa, setCgpa] = useState(3.5);
  const [domicileDistrict, setDomicileDistrict] = useState('Charsadda');

  const [agreeTerms, setAgreeTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [registeredSuccess, setRegisteredSuccess] = useState<any>(null);

  const calculatePasswordStrength = (pwd: string): { label: string; color: string; score: number } => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;

    if (score <= 1) return { label: 'Weak', color: 'bg-rose-500', score: 25 };
    if (score === 2) return { label: 'Fair', color: 'bg-amber-500', score: 50 };
    if (score === 3) return { label: 'Good', color: 'bg-sky-500', score: 75 };
    return { label: 'Strong', color: 'bg-emerald-500', score: 100 };
  };

  const strength = calculatePasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!agreeTerms) {
      setErrorMessage('You must agree to the Terms of Service and Privacy Policy.');
      return;
    }
    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }
    if (role === 'student' && (cgpa < 0 || cgpa > 4.0)) {
      setErrorMessage('CGPA must be between 0.0 and 4.0.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.register({
        email,
        password,
        full_name: fullName,
        role,
        university,
        degree_level: degreeLevel,
        discipline,
        current_semester: Number(currentSemester),
        cgpa: Number(cgpa),
        domicile_district: domicileDistrict
      });

      auth.setSession(res.token, res.user);
      setRegisteredSuccess(res);
      showToast('Registration successful! Welcome to SOI.', 'success');

      setTimeout(() => {
        if (role === 'student') {
          window.location.href = '/onboarding';
        } else {
          window.location.href = '/admin/dashboard';
        }
      }, 1500);
    } catch (err: any) {
      const msg = err.message || 'Registration failed.';
      setErrorMessage(msg);
      showToast(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  if (registeredSuccess) {
    return (
      <div className="w-full max-w-lg mx-auto bg-white dark:bg-slate-900 p-8 rounded-2xl border border-emerald-500/30 shadow-2xl text-center animate-fade-in">
        <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-3xl mx-auto mb-4">
          ✓
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Account Created!</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 max-w-sm mx-auto">
          Welcome, <span className="font-semibold text-slate-800 dark:text-slate-200">{registeredSuccess.user?.full_name}</span>.
          Your verification token has been issued. Launching your customized onboarding flow...
        </p>
        <div className="mt-6 flex justify-center">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-sky-600 dark:text-sky-400">
            <span className="w-4 h-4 border-2 border-sky-500/30 border-t-sky-500 rounded-full animate-spin"></span>
            Redirecting to setup...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-lg mx-auto bg-white dark:bg-slate-900 p-5 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl backdrop-blur-sm">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
          Create Your SOI Account
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Join thousands of university scholars unlocking verified opportunities across Pakistan and beyond.
        </p>
      </div>

      {/* Role Picker */}
      <div className="grid grid-cols-2 gap-2 p-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 mb-6">
        <button
          type="button"
          onClick={() => setRole('student')}
          className={`py-2 px-3 rounded-lg text-xs font-bold transition-all ${
            role === 'student'
              ? 'bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
          }`}
        >
          🎓 Student Scholar
        </button>
        <button
          type="button"
          onClick={() => setRole('admin')}
          className={`py-2 px-3 rounded-lg text-xs font-bold transition-all ${
            role === 'admin'
              ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
          }`}
        >
          ⚡ Administrator
        </button>
      </div>

      {errorMessage && (
        <div
          role="alert"
          className="mb-5 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2 animate-fade-in"
        >
          <span className="text-base font-bold leading-none">⚠️</span>
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Basic Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1" htmlFor="fullname">
              Full Name
            </label>
            <input
              id="fullname"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Ayesha Ahmad"
              className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1" htmlFor="reg-email">
              Email Address
            </label>
            <input
              id="reg-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. ayesha@uop.edu.pk"
              className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
            />
          </div>
        </div>

        {/* Student Specific Fields */}
        {role === 'student' && (
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-3">
            <div className="text-[11px] font-bold uppercase tracking-wider text-sky-600 dark:text-sky-400">
              Academic Eligibility & Quota Profile
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1" htmlFor="uni">
                  University / Institute
                </label>
                <input
                  id="uni"
                  type="text"
                  required
                  value={university}
                  onChange={(e) => setUniversity(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1" htmlFor="discipline">
                  Field / Discipline
                </label>
                <input
                  id="discipline"
                  type="text"
                  required
                  value={discipline}
                  onChange={(e) => setDiscipline(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1" htmlFor="sem">
                  Semester (1-8+)
                </label>
                <input
                  id="sem"
                  type="number"
                  min="1"
                  max="12"
                  required
                  value={currentSemester}
                  onChange={(e) => setCurrentSemester(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1" htmlFor="cgpa">
                  CGPA (0.0–4.0)
                </label>
                <input
                  id="cgpa"
                  type="number"
                  step="0.01"
                  min="0"
                  max="4.0"
                  required
                  value={cgpa}
                  onChange={(e) => setCgpa(Number(e.target.value))}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1" htmlFor="domicile">
                  District Domicile
                </label>
                <select
                  id="domicile"
                  value={domicileDistrict}
                  onChange={(e) => setDomicileDistrict(e.target.value)}
                  className="w-full px-2 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-xs"
                >
                  <option value="Charsadda">Charsadda (Priority)</option>
                  <option value="Peshawar">Peshawar</option>
                  <option value="Nowshera">Nowshera</option>
                  <option value="Mardan">Mardan</option>
                  <option value="Swat">Swat</option>
                  <option value="Abbottabad">Abbottabad</option>
                  <option value="Kohat">Kohat</option>
                  <option value="Khyber">Khyber (Merged)</option>
                  <option value="Bajaur">Bajaur (Merged)</option>
                  <option value="Islamabad">Islamabad</option>
                  <option value="Lahore">Lahore</option>
                  <option value="Other">Other District</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Passwords */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300" htmlFor="reg-pwd">
                Password
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <input
              id="reg-pwd"
              type={showPassword ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1" htmlFor="reg-confirm">
              Confirm Password
            </label>
            <input
              id="reg-confirm"
              type={showPassword ? 'text' : 'password'}
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat password"
              className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
            />
          </div>
        </div>

        {/* Password Strength Indicator */}
        {password && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span>Password strength:</span>
              <span className="font-semibold">{strength.label}</span>
            </div>
            <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${strength.color}`}
                style={{ width: `${strength.score}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Terms Checkbox */}
        <div className="pt-2">
          <label className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-600 dark:text-slate-400">
            <input
              type="checkbox"
              required
              checked={agreeTerms}
              onChange={(e) => setAgreeTerms(e.target.checked)}
              className="mt-0.5 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
            />
            <span>
              I agree to the{' '}
              <a href="/terms" target="_blank" className="text-sky-600 dark:text-sky-400 underline font-semibold">
                Terms of Service
              </a>{' '}
              and acknowledge the{' '}
              <a href="/privacy" target="_blank" className="text-sky-600 dark:text-sky-400 underline font-semibold">
                Privacy Policy
              </a>
              .
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-lg shadow-sky-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span>Creating Account...</span>
            </>
          ) : (
            <span>Complete Registration →</span>
          )}
        </button>
      </form>

      <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800 text-center text-xs text-slate-500 dark:text-slate-400">
        Already have an account?{' '}
        <a href="/login" className="font-bold text-sky-600 dark:text-sky-400 hover:underline">
          Sign In
        </a>
      </div>
    </div>
  );
}
