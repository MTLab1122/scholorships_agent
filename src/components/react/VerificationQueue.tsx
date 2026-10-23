import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Check,
  X,
  Flag,
  ExternalLink,
  RotateCw,
  AlertTriangle,
  Building
} from 'lucide-react';
import { api } from '../../lib/api';
import type { Opportunity } from '../../lib/types';
import { showToast } from './Toast';

export default function VerificationQueue() {
  const [queue, setQueue] = useState<Opportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [reviewingId, setReviewingId] = useState<string | null>(null);

  const loadQueue = async () => {
    setIsLoading(true);
    try {
      const data = await api.getVerificationQueue(50);
      setQueue(data);
    } catch (err) {
      console.error('Failed to load verification queue:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleDecision = async (id: string, decision: 'approve' | 'reject' | 'flag') => {
    const reason = prompt(`Enter review rationale for ${decision.toUpperCase()} action:`, 'Verified against official notification.');
    if (reason === null) return; // User cancelled

    setReviewingId(id);
    try {
      await api.reviewVerification(id, decision, reason);
      // Remove from active queue view
      setQueue((prev) => prev.filter((o) => o.id !== id));
      showToast(`Opportunity successfully marked as ${decision}`, 'success');
    } catch (err: any) {
      showToast(`Decision submission failed: ${err.message}`, 'error');
    } finally {
      setReviewingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
        <div className="inline-block w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-sm text-slate-500">Loading verification review queue...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div className="bg-amber-50 dark:bg-amber-950/30 p-4 rounded-xl border border-amber-200 dark:border-amber-900/50 flex items-start gap-3 text-amber-800 dark:text-amber-200">
        <ShieldAlert className="w-5 h-5 mt-0.5 text-amber-600 flex-shrink-0" />
        <div className="text-xs">
          <span className="font-bold block text-sm text-amber-900 dark:text-amber-100">
            Human-in-the-Loop Quality & Verification Queue
          </span>
          Uncertain records, anomalous claims, or tier-3 unofficial discovery items require administrative review before publication in official gazette reports. Review the evidence quotes and official domain links before approving.
        </div>
      </div>

      {queue.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500">
          <ShieldCheck className="w-12 h-12 mx-auto mb-2 text-emerald-500" />
          <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
            Verification Queue Clear
          </h3>
          <p className="text-xs mt-1">All active opportunity records have been verified against official sources.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {queue.map((item) => {
            const isProcessing = reviewingId === item.id;

            return (
              <div
                key={item.id}
                className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-4"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-700/60 pb-3">
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">
                      {item.name}
                    </h3>
                    <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                      <span>Sponsor: <strong>{item.sponsor}</strong></span>
                      <span>•</span>
                      <span>Category: <strong className="capitalize">{item.category}</strong></span>
                      <span>•</span>
                      <span>ID: <code>{item.id}</code></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDecision(item.id, 'approve')}
                      disabled={isProcessing}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Check className="w-3.5 h-3.5" /> Approve
                    </button>
                    <button
                      onClick={() => handleDecision(item.id, 'flag')}
                      disabled={isProcessing}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Flag className="w-3.5 h-3.5" /> Flag
                    </button>
                    <button
                      onClick={() => handleDecision(item.id, 'reject')}
                      disabled={isProcessing}
                      className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      <X className="w-3.5 h-3.5" /> Reject
                    </button>
                  </div>
                </div>

                {/* Evidence & Inspection Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  {/* Left: Extracted metadata */}
                  <div className="bg-slate-50 dark:bg-slate-900/40 p-3 rounded-lg border border-slate-200 dark:border-slate-700/60 space-y-1.5">
                    <span className="font-semibold text-slate-700 dark:text-slate-300 block">
                      Extracted Parameters:
                    </span>
                    <div>Sector Eligibility: <strong>{item.university_types}</strong></div>
                    <div>Eligible Semesters: <strong>{item.eligible_semesters?.length ? item.eligible_semesters.join(', ') : '1-8'}</strong></div>
                    <div>Stated Deadline: <strong>{item.deadline || 'not stated'}</strong></div>
                    <div>Charsadda / KP Flags: <strong>{item.charsadda_flag ? 'Charsadda (Yes)' : 'No'}, {item.kp_flag ? 'KP (Yes)' : 'No'}</strong></div>
                  </div>

                  {/* Right: Verbatim Evidence & Source */}
                  <div className="bg-sky-50 dark:bg-sky-950/30 p-3 rounded-lg border border-sky-100 dark:border-sky-900/50 space-y-2">
                    <span className="font-semibold text-sky-800 dark:text-sky-300 block">
                      Official Evidence Quote:
                    </span>
                    <p className="italic text-slate-700 dark:text-slate-300 leading-relaxed">
                      "{item.evidence_quote && item.evidence_quote !== 'not stated' ? item.evidence_quote : 'No verbatim text quote provided during extraction.'}"
                    </p>
                    {item.official_url && (
                      <a
                        href={item.official_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 font-medium text-sky-600 dark:text-sky-400 hover:underline pt-1"
                      >
                        <ExternalLink className="w-3 h-3" /> Inspect Stated Portal Link
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
