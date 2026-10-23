import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Play,
  RotateCw,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { api } from '../../lib/api';
import type { Schedule } from '../../lib/types';
import { showToast } from './Toast';

export default function SchedulesManager() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [successId, setSuccessId] = useState<string | null>(null);

  const loadSchedules = async () => {
    try {
      const data = await api.getSchedules();
      setSchedules(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSchedules();
  }, []);

  const handleTrigger = async (id: string) => {
    setTriggeringId(id);
    setSuccessId(null);
    showToast(`Triggering scheduled task ${id}...`, 'info');
    try {
      await api.triggerSchedule(id);
      setSuccessId(id);
      showToast(`Schedule ${id} triggered successfully`, 'success');
      setTimeout(() => setSuccessId(null), 3000);
    } catch (err: any) {
      showToast(`Trigger error: ${err.message}`, 'error');
    } finally {
      setTriggeringId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
        <div className="inline-block w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-sm text-slate-500">Loading automated background schedules...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {schedules.map((sched) => {
          const isRunning = triggeringId === sched.id;
          const isSuccess = successId === sched.id;

          return (
            <div
              key={sched.id}
              className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between text-xs space-y-4"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-sky-50 dark:bg-sky-950/50 text-sky-600 dark:text-sky-400 rounded-lg">
                      <Clock className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                        {sched.title}
                      </h3>
                      <span className="font-mono text-[10px] text-slate-400">
                        {sched.id}
                      </span>
                    </div>
                  </div>

                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/40">
                    {sched.status}
                  </span>
                </div>

                <div className="mt-3 space-y-1.5 text-slate-600 dark:text-slate-300">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Frequency:</span>
                    <strong className="text-slate-800 dark:text-slate-200">{sched.frequency}</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Timezone:</span>
                    <span>{sched.timezone}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Next Execution:</span>
                    <span className="text-sky-600 dark:text-sky-400 font-medium">{sched.next_run}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Last Run:</span>
                    <span>{sched.last_run}</span>
                  </div>
                </div>

                {isSuccess && (
                  <div className="mt-2 p-2 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 rounded font-medium flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Triggered successfully in background!
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-700 flex justify-end">
                <button
                  type="button"
                  onClick={() => handleTrigger(sched.id)}
                  disabled={isRunning}
                  className="flex items-center gap-1.5 px-3 py-1.5 font-semibold bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300 hover:bg-sky-100 rounded-lg border border-sky-200 dark:border-sky-800/40 transition-colors disabled:opacity-50"
                >
                  {isRunning ? (
                    <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3 h-3 fill-current" />
                  )}
                  Trigger Schedule Now
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
