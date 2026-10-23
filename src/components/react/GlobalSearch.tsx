import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, Award, Globe, User } from 'lucide-react';
import { api } from '../../lib/api';
import type { Opportunity, Source, StudentProfile } from '../../lib/types';

export default function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<{
    opportunities: Opportunity[];
    sources: Source[];
    students: StudentProfile[];
  }>({ opportunities: [], sources: [], students: [] });

  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcut listener ('/')
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === '/' &&
        document.activeElement?.tagName !== 'INPUT' &&
        document.activeElement?.tagName !== 'TEXTAREA'
      ) {
        e.preventDefault();
        inputRef.current?.focus();
      } else if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults({ opportunities: [], sources: [], students: [] });
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await api.search(query.trim());
        setResults(data);
        setIsOpen(true);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  const hasResults =
    results.opportunities.length > 0 ||
    results.sources.length > 0 ||
    results.students.length > 0;

  return (
    <div ref={searchRef} className="relative w-full max-w-md">
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (query.trim().length >= 2) setIsOpen(true);
          }}
          placeholder="Search opportunities, sources, agents (Press '/' to focus)..."
          className="w-full pl-10 pr-10 py-1.5 text-sm bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white dark:focus:bg-slate-800 transition-all"
        />
        {isLoading ? (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 animate-spin" />
        ) : (
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-200 dark:bg-slate-700 rounded border border-slate-300 dark:border-slate-600">
            /
          </kbd>
        )}
      </div>

      {isOpen && (
        <div className="absolute left-0 right-0 mt-2 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50 max-h-96 overflow-y-auto animate-fade-in">
          {!hasResults && !isLoading && (
            <div className="p-4 text-center text-sm text-slate-500 dark:text-slate-400">
              No matching records found for "{query}".
            </div>
          )}

          {results.opportunities.length > 0 && (
            <div className="p-2 border-b border-slate-100 dark:border-slate-700/50">
              <div className="px-2 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-sky-500" /> Opportunities ({results.opportunities.length})
              </div>
              {results.opportunities.slice(0, 5).map((opp) => (
                <a
                  key={opp.id}
                  href={`/admin/opportunities?search=${encodeURIComponent(opp.name)}`}
                  className="flex flex-col p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-200 line-clamp-1">
                    {opp.name}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {opp.sponsor} • {opp.category}
                  </span>
                </a>
              ))}
            </div>
          )}

          {results.sources.length > 0 && (
            <div className="p-2 border-b border-slate-100 dark:border-slate-700/50">
              <div className="px-2 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-emerald-500" /> Official Sources ({results.sources.length})
              </div>
              {results.sources.slice(0, 3).map((src) => (
                <a
                  key={src.url}
                  href="/admin/sources"
                  className="flex flex-col p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    {src.name}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">
                    {src.url}
                  </span>
                </a>
              ))}
            </div>
          )}

          {results.students.length > 0 && (
            <div className="p-2">
              <div className="px-2 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-violet-500" /> Students ({results.students.length})
              </div>
              {results.students.slice(0, 3).map((stu) => (
                <a
                  key={stu.id}
                  href="/admin/students"
                  className="flex flex-col p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    {stu.full_name}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {stu.university} • Semester {stu.current_semester} ({stu.discipline})
                  </span>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
