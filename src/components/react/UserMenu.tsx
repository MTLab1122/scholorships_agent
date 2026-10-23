import React, { useState, useEffect, useRef } from 'react';
import { auth } from '../../lib/auth';
import type { User } from '../../lib/types';

interface UserMenuProps {
  currentRole: 'admin' | 'student';
}

export default function UserMenu({ currentRole }: UserMenuProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initial fetch from client storage
    setUser(auth.getUser());

    const handleAuthChange = (e: any) => {
      setUser(e.detail?.user || null);
    };

    window.addEventListener('soi_auth_changed', handleAuthChange);

    // Click outside listener
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      window.removeEventListener('soi_auth_changed', handleAuthChange);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    await auth.logout();
  };

  const displayName = user?.full_name || (currentRole === 'admin' ? 'Administrator' : 'Student Scholar');
  const displayRole = user?.role ? (user.role === 'admin' ? 'Admin' : 'Scholar') : (currentRole === 'admin' ? 'Admin' : 'Student');
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || (currentRole === 'admin' ? 'AD' : 'ST');

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1 pl-1.5 pr-2.5 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors text-xs"
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label="User Account Menu"
      >
        <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-600 text-white font-bold flex items-center justify-center text-[10px] shadow-sm">
          {initials}
        </div>
        <span className="font-semibold text-slate-800 dark:text-slate-200 hidden sm:inline max-w-[120px] truncate">
          {displayName}
        </span>
        <span className="text-[10px] text-slate-400">▾</span>
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-56 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl py-2 z-50 animate-fade-in text-xs"
        >
          {/* User Header */}
          <div className="px-4 py-2.5 border-b border-slate-100 dark:border-slate-800">
            <div className="font-bold text-slate-900 dark:text-white truncate">
              {displayName}
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
              {user?.email || (currentRole === 'admin' ? 'admin@opportunity.edu.pk' : 'student@opportunity.edu.pk')}
            </div>
            <div className="mt-1.5 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 border border-sky-200 dark:border-sky-800/60">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>Role: {displayRole}</span>
              {user?.is_verified && <span className="ml-1 text-emerald-500">✓ Verified</span>}
            </div>
          </div>

          {/* Quick Links */}
          <div className="py-1">
            {currentRole === 'student' ? (
              <>
                <a
                  href="/student/profile"
                  className="flex items-center gap-2 px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <span>👤</span>
                  <span>My Profile & Standing</span>
                </a>
                <a
                  href="/student/saved"
                  className="flex items-center gap-2 px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <span>🔖</span>
                  <span>Saved Bookmarks</span>
                </a>
                <a
                  href="/onboarding"
                  className="flex items-center gap-2 px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <span>✨</span>
                  <span>Rerun Onboarding Setup</span>
                </a>
              </>
            ) : (
              <>
                <a
                  href="/admin/settings"
                  className="flex items-center gap-2 px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <span>⚙️</span>
                  <span>System Settings</span>
                </a>
                <a
                  href="/admin/backups"
                  className="flex items-center gap-2 px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <span>🗄️</span>
                  <span>Database Backups</span>
                </a>
              </>
            )}

            <div className="border-t border-slate-100 dark:border-slate-800 my-1"></div>

            <a
              href="/privacy"
              className="flex items-center gap-2 px-4 py-1.5 text-[11px] text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
            >
              <span>🛡️</span>
              <span>Privacy Policy</span>
            </a>
            <a
              href="/terms"
              className="flex items-center gap-2 px-4 py-1.5 text-[11px] text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
            >
              <span>📜</span>
              <span>Terms of Service</span>
            </a>
          </div>

          {/* Logout Action */}
          <div className="pt-1 border-t border-slate-100 dark:border-slate-800">
            <button
              type="button"
              onClick={handleLogout}
              className="w-full text-left flex items-center gap-2 px-4 py-2 text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
            >
              <span>🚪</span>
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
