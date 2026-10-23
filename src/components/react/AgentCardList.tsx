import React, { useState, useEffect } from 'react';
import {
  Bot,
  Play,
  RotateCw,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Clock,
  Activity,
  Sliders
} from 'lucide-react';
import { api } from '../../lib/api';
import type { AIAgent } from '../../lib/types';
import { showToast } from './Toast';

export default function AgentCardList() {
  const [agents, setAgents] = useState<AIAgent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [runningAgentId, setRunningAgentId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ id: string; msg: string; type: 'success' | 'error' } | null>(null);

  const loadAgents = async () => {
    try {
      const data = await api.getAgents();
      setAgents(data || []);
    } catch (err: any) {
      showToast(err.message || 'Failed to load agents.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleRunAgent = async (agentId: string) => {
    setRunningAgentId(agentId);
    setStatusMessage(null);
    try {
      const res = await api.runAgent(agentId);
      const msg = res.message || 'Task completed successfully.';
      setStatusMessage({
        id: agentId,
        msg: `Execution SUCCESS: ${msg}`,
        type: 'success'
      });
      showToast(`Agent [${agentId}] completed execution!`, 'success');
      loadAgents();
    } catch (err: any) {
      const errTxt = err.message || 'Execution failed';
      setStatusMessage({
        id: agentId,
        msg: `Failed: ${errTxt}`,
        type: 'error'
      });
      showToast(`Agent [${agentId}] error: ${errTxt}`, 'error');
    } finally {
      setRunningAgentId(null);
    }
  };


  if (isLoading) {
    return (
      <div className="p-12 text-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
        <div className="inline-block w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-sm text-slate-500">Loading AI Agent registry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-sky-900 to-indigo-950 p-6 rounded-2xl text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold uppercase tracking-wider">
            <Activity className="w-4 h-4" /> Multi-Agent Autonomous Fleet
          </div>
          <h2 className="text-xl font-bold mt-1">15 Specialized AI Agents</h2>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Coordinated autonomous agents responsible for source discovery, structured extraction, eligibility verification, fraud protection, personalized matching, and 20-report compilation.
          </p>
        </div>
        <button
          onClick={() => handleRunAgent('orchestrator')}
          disabled={runningAgentId === 'orchestrator'}
          className="flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold rounded-xl shadow-lg shadow-sky-500/20 transition-all disabled:opacity-50"
        >
          {runningAgentId === 'orchestrator' ? (
            <RotateCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4 fill-current" />
          )}
          Run Master Orchestrator Cycle
        </button>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => {
          const isRunning = runningAgentId === agent.id;
          const isMessageForMe = statusMessage?.id === agent.id;

          return (
            <div
              key={agent.id}
              className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between hover:border-sky-300 dark:hover:border-sky-600 transition-all"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-sky-50 dark:bg-sky-950/50 text-sky-600 dark:text-sky-400 rounded-lg">
                      <Bot className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 line-clamp-1">
                        {agent.name}
                      </h3>
                      <div className="text-[11px] font-mono text-slate-400">
                        {agent.id}
                      </div>
                    </div>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                      agent.status === 'operational'
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/40'
                        : 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800/40'
                    }`}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    {agent.status}
                  </span>
                </div>

                <p className="mt-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed min-h-[3rem]">
                  {agent.purpose}
                </p>

                <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700/60 space-y-1 text-xs text-slate-500">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1">
                      <Cpu className="w-3.5 h-3.5 text-slate-400" /> Model:
                    </span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">
                      {agent.model}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" /> Failures:
                    </span>
                    <span className="text-slate-700 dark:text-slate-300">
                      {agent.failure_count}
                    </span>
                  </div>
                </div>

                {isMessageForMe && (
                  <div
                    className={`mt-2 p-2 rounded text-xs ${
                      statusMessage.type === 'success'
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300'
                        : 'bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300'
                    }`}
                  >
                    {statusMessage.msg}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  Actions: {agent.supported_actions.join(', ')}
                </span>
                <button
                  onClick={() => handleRunAgent(agent.id)}
                  disabled={isRunning}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300 hover:bg-sky-100 rounded-lg border border-sky-200 dark:border-sky-800/50 transition-colors disabled:opacity-50"
                >
                  {isRunning ? (
                    <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3 h-3 fill-current" />
                  )}
                  Run Now
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
