import React, { useState, useEffect } from 'react';
import {
  Globe,
  Plus,
  RotateCw,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { api } from '../../lib/api';
import type { Source } from '../../lib/types';
import { showToast } from './Toast';

export default function SourceManager() {
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [testResults, setTestResults] = useState<Record<string, { status: number; loading?: boolean }>>({});
  const [showAddModal, setShowAddModal] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('university');
  const [tier, setTier] = useState(1);

  const loadSources = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSources();
      setSources(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleTestSource = async (sourceUrl: string) => {
    setTestResults((prev) => ({ ...prev, [sourceUrl]: { status: 0, loading: true } }));
    try {
      const res = await api.testSource(sourceUrl);
      setTestResults((prev) => ({ ...prev, [sourceUrl]: { status: res.status, loading: false } }));
      showToast(`Source responded with HTTP ${res.status}`, res.status === 200 ? 'success' : 'warning');
    } catch (err) {
      setTestResults((prev) => ({ ...prev, [sourceUrl]: { status: 500, loading: false } }));
      showToast(`Source connection failed`, 'error');
    }
  };

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !url) return;
    try {
      await api.addSource({ name, url, category, tier });
      setShowAddModal(false);
      setName('');
      setUrl('');
      showToast('Source added successfully', 'success');
      loadSources();
    } catch (err: any) {
      showToast(`Failed to add source: ${err.message}`, 'error');
    }
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
        <div className="inline-block w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-sm text-slate-500">Loading verified source registry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Registered Research Sources & University Portals
          </h2>
          <p className="text-xs text-slate-500">
            Official government portals, HEC feeds, and accredited Pakistani university scholarship pages.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-sky-600 hover:bg-sky-700 text-white rounded-lg transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" /> Add Official Source
        </button>
      </div>

      {/* Sources Table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-700 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Source & Domain</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Trust Tier</th>
                <th className="py-3 px-4">Consecutive Failures</th>
                <th className="py-3 px-4 text-right">Connectivity Test</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
              {sources.map((src) => {
                const test = testResults[src.url];
                return (
                  <tr key={src.url} className="hover:bg-slate-50/60 dark:hover:bg-slate-750 transition-colors">
                    <td className="py-3 px-4 max-w-sm">
                      <div className="font-semibold text-slate-900 dark:text-slate-100">{src.name}</div>
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[11px] text-sky-600 dark:text-sky-400 hover:underline flex items-center gap-1 mt-0.5 line-clamp-1"
                      >
                        <ExternalLink className="w-3 h-3 flex-shrink-0" /> {src.url}
                      </a>
                    </td>
                    <td className="py-3 px-4 capitalize text-slate-700 dark:text-slate-300">
                      {src.category}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border border-sky-200 dark:border-sky-800/40">
                        <ShieldCheck className="w-3 h-3" /> Tier {src.tier || 1}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {src.consecutive_failures && src.consecutive_failures > 0 ? (
                        <span className="inline-flex items-center gap-1 text-rose-600 font-semibold">
                          <AlertTriangle className="w-3.5 h-3.5" /> {src.consecutive_failures} fails
                        </span>
                      ) : (
                        <span className="text-emerald-600 font-medium">0 (Healthy)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {test ? (
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-bold ${
                            test.status === 200
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                              : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                          }`}
                        >
                          {test.loading ? (
                            <RotateCw className="w-3 h-3 animate-spin" />
                          ) : test.status === 200 ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : (
                            <XCircle className="w-3 h-3" />
                          )}
                          HTTP {test.status || 'Checking...'}
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleTestSource(src.url)}
                          className="px-2.5 py-1 text-[11px] font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700/60 rounded hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-600"
                        >
                          Ping Test
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Source Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-700 space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Register New Official Opportunity Source
            </h3>
            <form onSubmit={handleAddSource} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Source Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. UET Peshawar Financial Aid Office"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Portal URL (.gov.pk or .edu.pk)
                </label>
                <input
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://uetpeshawar.edu.pk/scholarships"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
                  >
                    <option value="university">University Official</option>
                    <option value="government">Government Education</option>
                    <option value="foundation">Accredited Foundation</option>
                    <option value="international">International Body</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                    Trust Tier
                  </label>
                  <select
                    value={tier}
                    onChange={(e) => setTier(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
                  >
                    <option value={1}>Tier 1: Official Domain</option>
                    <option value={2}>Tier 2: Official Partner</option>
                    <option value={3}>Tier 3: Discovery Feed</option>
                  </select>
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-slate-100 dark:border-slate-700">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-1.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 font-semibold bg-sky-600 text-white rounded-lg hover:bg-sky-700"
                >
                  Save Source
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
