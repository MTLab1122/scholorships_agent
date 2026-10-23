import React, { useState, useEffect } from 'react';
import {
  Kanban,
  CheckSquare,
  Clock,
  ArrowRight,
  Plus,
  Building,
  FileCheck2,
  Calendar,
  FileText
} from 'lucide-react';
import { api } from '../../lib/api';
import type { ApplicationRecord } from '../../lib/types';
import { showToast } from './Toast';

const STAGES = [
  'Discovered',
  'Saved',
  'Checking Eligibility',
  'Preparing',
  'Submitted',
  'Under Review',
  'Shortlisted',
  'Interview',
  'Result: Awarded'
];

interface ApplicationKanbanProps {
  studentId: string;
}

export default function ApplicationKanban({ studentId }: ApplicationKanbanProps) {
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadApplications = async () => {
    try {
      const data = await api.getApplications(studentId);
      setApplications(data || []);
    } catch (err: any) {
      showToast(err.message || 'Failed to load applications.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, [studentId]);

  const handleMoveStage = async (appId: string, currentStage: string) => {
    const currentIndex = STAGES.indexOf(currentStage);
    const nextStage = STAGES[(currentIndex + 1) % STAGES.length];

    try {
      await api.updateApplication(appId, nextStage);
      setApplications((prev) =>
        prev.map((a) => (a.id === appId ? { ...a, stage: nextStage } : a))
      );
      showToast(`Application moved to "${nextStage}"`, 'success');
    } catch (err: any) {
      showToast(`Stage update failed: ${err.message}`, 'error');
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 space-y-4">
        <div className="flex justify-between items-center">
          <div className="h-5 w-48 skeleton"></div>
          <div className="h-5 w-24 skeleton"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-64 rounded-xl border border-slate-200 dark:border-slate-800 p-3 space-y-3">
              <div className="h-4 w-20 skeleton"></div>
              <div className="h-20 w-full skeleton"></div>
              <div className="h-20 w-full skeleton"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Kanban className="w-5 h-5 text-sky-500" /> 9-Stage Application Tracker
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Organize every scholarship and internship application through its full admission or award cycle.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="/student/opportunities"
            className="text-xs font-bold text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/40 px-3 py-1.5 rounded-xl border border-sky-200 dark:border-sky-800/60 hover:bg-sky-100 transition-colors"
          >
            + Track More Opportunities
          </a>
          <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
            {applications.length} Total Tracked
          </div>
        </div>
      </div>

      {applications.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 flex items-center justify-center text-3xl mx-auto">
            📋
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Your Application Board is Clean
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            You are not tracking any active opportunities yet. Browse scholarships or matches to add your first target program.
          </p>
          <div className="pt-2">
            <a
              href="/student/opportunities"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-sky-500 hover:bg-sky-400 text-white rounded-xl shadow-md transition-all"
            >
              Explore Opportunities →
            </a>
          </div>
        </div>
      ) : (
        /* Kanban Horizontal Board */
        <div className="flex gap-4 overflow-x-auto pb-4 pt-1">
          {STAGES.map((stage) => {
            const stageApps = applications.filter(
              (a) => (a.stage || '').toLowerCase() === stage.toLowerCase()
            );

            return (
              <div
                key={stage}
                className="w-72 flex-shrink-0 bg-slate-50/80 dark:bg-slate-900/60 rounded-2xl border border-slate-200 dark:border-slate-800 p-3.5 flex flex-col max-h-[75vh]"
              >
                {/* Column Header */}
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60 dark:border-slate-800 text-xs">
                  <span className="font-bold text-slate-700 dark:text-slate-300">
                    {stage}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {stageApps.length}
                  </span>
                </div>

                {/* Cards Container */}
                <div className="space-y-2.5 overflow-y-auto flex-1 pr-1">
                  {stageApps.length === 0 ? (
                    <div className="py-8 text-center text-xs text-slate-400 italic">
                      No applications in this stage
                    </div>
                  ) : (
                    stageApps.map((app) => (
                      <div
                        key={app.id}
                        className="bg-white dark:bg-slate-800 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-2.5 hover:border-sky-400 dark:hover:border-sky-500 transition-all text-xs card-hover-3d"
                      >
                        <div>
                          <h4 className="font-bold text-slate-900 dark:text-slate-100 line-clamp-2">
                            {app.opportunity_name}
                          </h4>
                          <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                            {app.sponsor}
                          </div>
                        </div>

                        {app.application_deadline && (
                          <div className="flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400">
                            <Calendar className="w-3 h-3" /> Deadline: {app.application_deadline}
                          </div>
                        )}

                        <div className="flex items-center gap-1.5 pt-1">
                          {/* Advance Stage button */}
                          <button
                            type="button"
                            onClick={() => handleMoveStage(app.id, app.stage)}
                            className="flex-1 flex items-center justify-center gap-1 py-1 px-2 text-[11px] font-semibold bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 rounded-lg hover:bg-sky-100 transition-colors border border-sky-200 dark:border-sky-800/40"
                          >
                            Advance <ArrowRight className="w-3 h-3" />
                          </button>

                          {/* Prep link */}
                          <a
                            href={`/student/prep?opp=${encodeURIComponent(app.opportunity_id)}`}
                            className="p-1 px-2 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700/60 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                            title="Generate document prep packet"
                          >
                            <FileText className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
