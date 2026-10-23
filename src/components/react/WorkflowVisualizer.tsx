import React, { useState } from 'react';
import {
  GitFork,
  Play,
  RotateCw,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Search,
  FileText,
  UserCheck
} from 'lucide-react';
import { api } from '../../lib/api';
import { showToast } from './Toast';

const STAGES = [
  { id: 'discovery', name: 'Discovery', desc: 'Crawls official .gov.pk / .edu.pk domains', icon: Search },
  { id: 'extraction', name: 'Extraction', desc: 'Extracts structured records with quotes', icon: FileText },
  { id: 'classification', name: 'Taxonomy', desc: 'Classifies categories, sectors & degrees', icon: GitFork },
  { id: 'verification', name: 'Verification', desc: 'Verifies trust tier & HTTP reachability', icon: ShieldCheck },
  { id: 'matching', name: 'Matching', desc: 'Semester-wise student eligibility matching', icon: UserCheck },
  { id: 'reports', name: '20-Reports', desc: 'Compiles vector PDF, Excel & CSV files', icon: FileText }
];

export default function WorkflowVisualizer() {
  const [isRunning, setIsRunning] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);

  const handleRunFullCycle = async () => {
    setIsRunning(true);
    setLastResult(null);
    showToast('Triggering full pipeline execution across 15 agents...', 'info');
    try {
      const res = await api.runAgent('orchestrator');
      setLastResult(res);
      showToast('Pipeline execution finished successfully!', 'success');
    } catch (err: any) {
      showToast(`Pipeline execution error: ${err.message}`, 'error');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <GitFork className="w-5 h-5 text-sky-500" /> Autonomous Multi-Agent Pipeline Topology
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Sequential quality-gated workflow governing data discovery, LLM structured extraction, strict eligibility verification, deduplication, personalized ranking, and 20-report file generation.
          </p>
        </div>
        <button
          onClick={handleRunFullCycle}
          disabled={isRunning}
          className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold bg-sky-600 hover:bg-sky-700 text-white rounded-xl shadow-sm transition-colors disabled:opacity-50"
        >
          {isRunning ? (
            <RotateCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4 fill-current" />
          )}
          {isRunning ? 'Orchestrating Cycle...' : 'Run Autonomous Cycle'}
        </button>
      </div>

      {/* Visual Pipeline Stages */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          return (
            <div
              key={stage.id}
              className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between relative group hover:border-sky-400 dark:hover:border-sky-500 transition-all text-xs"
            >
              <div>
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="font-mono text-[10px] font-bold">STAGE 0{idx + 1}</span>
                  <Icon className="w-4 h-4 text-sky-500" />
                </div>
                <h4 className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  {stage.name}
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  {stage.desc}
                </p>
              </div>

              <div className="mt-4 pt-2 border-t border-slate-100 dark:border-slate-700 flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> Quality Gated
              </div>
            </div>
          );
        })}
      </div>

      {lastResult && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200 dark:border-emerald-800/50 text-xs text-emerald-800 dark:text-emerald-200">
          <span className="font-bold block text-sm mb-1">
            Orchestrator Cycle Complete!
          </span>
          <pre className="mt-2 p-3 bg-emerald-950 text-emerald-200 rounded-lg overflow-x-auto font-mono text-[11px]">
            {JSON.stringify(lastResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
