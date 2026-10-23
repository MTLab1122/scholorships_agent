import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  RotateCw,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  FileCode,
  Calendar,
  Sparkles,
  Layers
} from 'lucide-react';
import { api } from '../../lib/api';
import type { ReportDefinition } from '../../lib/types';
import { showToast } from './Toast';

export default function ReportManager() {
  const [reports, setReports] = useState<ReportDefinition[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [generatingReportNum, setGeneratingReportNum] = useState<string | null>(null);
  const [selectedFormats, setSelectedFormats] = useState<Record<string, string[]>>({});
  const [generationResults, setGenerationResults] = useState<Record<string, any>>({});

  useEffect(() => {
    api.getReports()
      .then((data) => {
        setReports(data || []);
        const defaults: Record<string, string[]> = {};
        (data || []).forEach((r) => {
          defaults[r.number] = ['pdf', 'xlsx', 'csv', 'html'];
        });
        setSelectedFormats(defaults);
      })
      .catch((e) => {
        console.error(e);
        showToast('Failed to load reports catalog.', 'error');
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handleGenerate = async (reportNum: string) => {
    setGeneratingReportNum(reportNum);
    try {
      const formats = selectedFormats[reportNum] || ['pdf', 'xlsx', 'csv', 'html'];
      const res = await api.generateReport(reportNum, formats);
      setGenerationResults((prev) => ({
        ...prev,
        [reportNum]: res
      }));
      showToast(`Report ${reportNum} generated successfully!`, 'success');
    } catch (err: any) {
      showToast(`Generation failed: ${err.message}`, 'error');
    } finally {
      setGeneratingReportNum(null);
    }
  };

  const toggleFormat = (reportNum: string, fmt: string) => {
    setSelectedFormats((prev) => {
      const current = prev[reportNum] || ['pdf', 'xlsx', 'csv', 'html'];
      const next = current.includes(fmt)
        ? current.filter((f) => f !== fmt)
        : [...current, fmt];
      return { ...prev, [reportNum]: next };
    });
  };

  if (isLoading) {
    return (
      <div className="p-12 text-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
        <div className="inline-block w-8 h-8 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-sm text-slate-500">Loading 20-Report Catalog...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-sky-950 p-6 rounded-2xl text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold uppercase tracking-wider">
            <Layers className="w-4 h-4" /> Comprehensive Multi-Format Publisher
          </div>
          <h2 className="text-xl font-bold mt-1">20 Report Publication Center</h2>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Automated compilation for all 20 standardized reports. Generates publication-grade Vector PDFs (ReportLab), multi-tab Excel sheets, standard CSV, and responsive HTML digests.
          </p>
        </div>
      </div>

      {/* 20 Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((report) => {
          const isGenerating = generatingReportNum === report.number;
          const result = generationResults[report.number];
          const formats = selectedFormats[report.number] || ['pdf', 'xlsx', 'csv', 'html'];

          return (
            <div
              key={report.number}
              className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between hover:border-sky-300 dark:hover:border-sky-600 transition-all"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 font-bold text-xs">
                      {report.number}
                    </span>
                    <div>
                      <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                        {report.title}
                      </h3>
                      <span className="text-[11px] text-slate-400 capitalize">
                        {report.category} • {report.frequency}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="mt-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed min-h-[2.5rem]">
                  {report.description}
                </p>

                {/* Target Audience & Filter Summary */}
                <div className="mt-3 py-2 px-3 bg-slate-50 dark:bg-slate-900/40 rounded-lg text-xs text-slate-500 space-y-1">
                  <div>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">Audience:</span> {report.audience}
                  </div>
                </div>

                {/* Format Checkboxes */}
                <div className="mt-3 flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Formats:</span>
                  {['pdf', 'xlsx', 'csv', 'html'].map((fmt) => (
                    <button
                      key={fmt}
                      type="button"
                      onClick={() => toggleFormat(report.number, fmt)}
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold uppercase transition-colors ${
                        formats.includes(fmt)
                          ? 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300 border border-sky-300 dark:border-sky-700'
                          : 'bg-slate-100 text-slate-400 dark:bg-slate-800'
                      }`}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>
              </div>

              {/* Action and Download Area */}
              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/60">
                {result ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                      <CheckCircle2 className="w-4 h-4" /> Generated {result.record_count} verified opportunities!
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(result.generated_files || {}).map(([fmt, path]: any) => (
                        <a
                          key={fmt}
                          href={`/api/reports/download?path=${encodeURIComponent(path)}`}
                          download
                          className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 rounded border border-emerald-200 dark:border-emerald-800/50 hover:bg-emerald-100 uppercase"
                        >
                          <Download className="w-3 h-3" /> {fmt}
                        </a>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-400">
                      Vector PDF / Excel Engine
                    </span>
                    <button
                      type="button"
                      onClick={() => handleGenerate(report.number)}
                      disabled={isGenerating || formats.length === 0}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-sky-600 hover:bg-sky-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      {isGenerating ? (
                        <RotateCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                      )}
                      {isGenerating ? 'Compiling...' : 'Generate Now'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
