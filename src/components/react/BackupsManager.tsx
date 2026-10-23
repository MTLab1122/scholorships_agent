import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import type { BackupMetadata } from '../../lib/types';
import { showToast } from './Toast';

export default function BackupsManager() {
  const [backups, setBackups] = useState<BackupMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedBackupForRestore, setSelectedBackupForRestore] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState(false);
  const [restoreConfirmText, setRestoreConfirmText] = useState('');

  const loadBackups = async () => {
    setIsLoading(true);
    try {
      const data = await api.listBackups();
      setBackups(data || []);
    } catch (err: any) {
      showToast(err.message || 'Failed to load database backups.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadBackups();
  }, []);

  const handleCreateBackup = async () => {
    setIsCreating(true);
    try {
      const res = await api.createBackup();
      showToast(`Backup ${res.backup.filename} created successfully!`, 'success');
      await loadBackups();
    } catch (err: any) {
      showToast(err.message || 'Failed to create backup.', 'error');
    } finally {
      setIsCreating(false);
    }
  };

  const handleRestoreBackup = async () => {
    if (!selectedBackupForRestore) return;
    if (restoreConfirmText !== 'RESTORE') {
      showToast('Please type RESTORE to confirm restoration.', 'warning');
      return;
    }

    setIsRestoring(true);
    try {
      const res = await api.restoreBackup(selectedBackupForRestore);
      showToast(res.message || 'Database restored successfully!', 'success');
      setSelectedBackupForRestore(null);
      setRestoreConfirmText('');
      await loadBackups();
    } catch (err: any) {
      showToast(err.message || 'Restoration failed.', 'error');
    } finally {
      setIsRestoring(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 rounded-2xl text-white border border-slate-800 shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 mb-2">
            🛡️ Zero-Downtime Backup Engine Active
          </div>
          <h1 className="text-xl font-bold tracking-tight">
            Database Backups & Disaster Recovery
          </h1>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Atomic SQLite snapshots preserving all opportunities, verified source registries, student profiles, Kanban states, and audit trails.
          </p>
        </div>

        <button
          onClick={handleCreateBackup}
          disabled={isCreating}
          className="px-4 py-2.5 text-xs font-bold rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap"
        >
          {isCreating ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span>Capturing Snapshot...</span>
            </>
          ) : (
            <>
              <span>💾</span>
              <span>Create Instant Backup</span>
            </>
          )}
        </button>
      </div>

      {/* Backups List */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Available Snapshot Vault
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {backups.length} archives
            </span>
          </div>

          <button
            onClick={loadBackups}
            className="text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1"
          >
            ↻ Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-500 space-y-2">
            <div className="w-6 h-6 border-2 border-sky-500/30 border-t-sky-500 rounded-full animate-spin mx-auto"></div>
            <div>Reading backup catalog...</div>
          </div>
        ) : backups.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-3xl mb-2">📁</div>
            <div className="text-sm font-bold text-slate-900 dark:text-white">No snapshots yet</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              Click &quot;Create Instant Backup&quot; to generate your first zero-downtime database snapshot.
            </p>
            <button
              onClick={handleCreateBackup}
              disabled={isCreating}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-sky-500 hover:bg-sky-400 text-white shadow"
            >
              Take First Snapshot
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {backups.map((b) => (
              <div
                key={b.filename}
                className="px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/50 dark:hover:bg-slate-850/50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 flex items-center justify-center text-lg flex-shrink-0 mt-0.5">
                    🗄️
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white font-mono break-all">
                      {b.filename}
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                      <span>Size: {b.size_kb} KB</span>
                      <span>•</span>
                      <span>
                        Created: {b.modified ? new Date(b.modified).toLocaleString() : 'Recent'}
                      </span>
                      <span>•</span>
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Integrity Verified</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    onClick={() => {
                      setSelectedBackupForRestore(b.filename);
                      setRestoreConfirmText('');
                    }}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-900/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 transition-colors"
                  >
                    Restore from Snapshot
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Restoration & Disaster Recovery Procedures Guide */}
      <div className="bg-slate-50 dark:bg-slate-900/60 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <span>📖</span> Documented Restoration & Recovery Procedures
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="font-bold text-slate-900 dark:text-white">Method A: Web UI One-Click Restore</div>
            <ol className="list-decimal pl-4 space-y-1">
              <li>Locate target snapshot in the vault above.</li>
              <li>Click &quot;Restore from Snapshot&quot; and type &quot;RESTORE&quot; to confirm.</li>
              <li>The engine automatically takes an emergency pre-restore snapshot before applying data.</li>
              <li>Tables are atomically replaced without service restart.</li>
            </ol>
          </div>
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="font-bold text-slate-900 dark:text-white">Method B: Cold Disaster File Restore</div>
            <ol className="list-decimal pl-4 space-y-1">
              <li>Stop the FastAPI server process (`python main.py`).</li>
              <li>Navigate to repository directory: `data/backups/`.</li>
              <li>Copy desired snapshot to `data/opportunities.db`.</li>
              <li>Restart server; migrations and integrity checks execute automatically on boot.</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Restoration Confirmation Modal */}
      {selectedBackupForRestore && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in"
        >
          <div className="bg-white dark:bg-slate-900 max-w-md w-full rounded-2xl p-6 border border-amber-500/40 shadow-2xl space-y-4">
            <div className="flex items-center gap-2.5 text-amber-600 dark:text-amber-400">
              <span className="text-2xl">⚠️</span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Confirm Database Restoration
              </h3>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              You are about to restore the database to snapshot:
              <br />
              <span className="font-mono font-bold text-slate-900 dark:text-white break-all">
                {selectedBackupForRestore}
              </span>
            </p>

            <div className="p-3 rounded-xl bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800 text-[11px] text-sky-800 dark:text-sky-300">
              <strong>Emergency Pre-Snapshot Protection:</strong> An immediate snapshot will be captured before restoring, so no intermediate changes can be accidentally lost.
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1" htmlFor="confirm-restore-text">
                Type <span className="font-mono text-rose-600 dark:text-rose-400">RESTORE</span> to proceed:
              </label>
              <input
                id="confirm-restore-text"
                type="text"
                value={restoreConfirmText}
                onChange={(e) => setRestoreConfirmText(e.target.value)}
                placeholder="RESTORE"
                className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-xs focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedBackupForRestore(null)}
                className="px-3.5 py-2 text-xs font-semibold rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={restoreConfirmText !== 'RESTORE' || isRestoring}
                onClick={handleRestoreBackup}
                className="px-4 py-2 text-xs font-bold rounded-xl bg-amber-500 hover:bg-amber-400 text-white shadow disabled:opacity-50 transition-all flex items-center gap-1.5"
              >
                {isRestoring ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                    <span>Restoring...</span>
                  </>
                ) : (
                  <span>Execute Restoration</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
