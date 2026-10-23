import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ExternalLink,
  Bookmark,
  CheckCircle2,
  AlertTriangle,
  Clock,
  X,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Building,
  GraduationCap
} from 'lucide-react';
import { api } from '../../lib/api';
import type { Opportunity } from '../../lib/types';
import { showToast } from './Toast';


interface OpportunityTableProps {
  isAdmin?: boolean;
  initialSearch?: string;
  studentId?: string;
}

export default function OpportunityTable({
  isAdmin = false,
  initialSearch = '',
  studentId
}: OpportunityTableProps) {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState(initialSearch);
  const [category, setCategory] = useState('');
  const [sector, setSector] = useState('');
  const [semester, setSemester] = useState('');
  const [status, setStatus] = useState('');
  const [charsaddaOnly, setCharsaddaOnly] = useState(false);
  const [kpOnly, setKpOnly] = useState(false);

  // Drawer details
  const [selectedOpp, setSelectedOpp] = useState<Opportunity | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  // Load opportunities
  const loadOpportunities = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getOpportunities({
        category: category || undefined,
        status: status || undefined,
        university_type: sector || undefined,
        semester: semester ? Number(semester) : undefined
      });
      setOpportunities(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load opportunities');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [category, sector, semester, status]);

  // Load saved opportunities for student
  useEffect(() => {
    if (studentId) {
      api.getSavedOpportunities(studentId)
        .then((saved) => setSavedIds(new Set(saved.map((o) => o.id))))
        .catch((e) => console.error('Failed to load saved:', e));
    }
  }, [studentId]);

  // Handle bookmark
  const toggleBookmark = async (oppId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const sid = studentId || 'STU-1792427107';
    try {
      const res = await api.toggleSavedOpportunity(sid, oppId);
      setSavedIds((prev) => {
        const next = new Set(prev);
        if (res.is_saved) {
          next.add(oppId);
          showToast('Opportunity saved to bookmarks!', 'success');
        } else {
          next.delete(oppId);
          showToast('Removed from bookmarks.', 'info');
        }
        return next;
      });
    } catch (err: any) {
      showToast(`Bookmark error: ${err.message}`, 'error');
    }
  };

  const handleAddToTracker = async () => {
    if (!selectedOpp) return;
    const sid = studentId || 'STU-1792427107';
    try {
      await api.createApplication({
        student_id: sid,
        opportunity_id: selectedOpp.id,
        opportunity_name: selectedOpp.name,
        sponsor: selectedOpp.sponsor,
        stage: 'interested'
      });
      showToast(`Added "${selectedOpp.name}" to your Kanban tracker!`, 'success');
    } catch (err: any) {
      showToast(err.message || 'Opportunity is already tracked.', 'info');
    }
  };


  // Filter client-side by text and priority flags
  const filtered = opportunities.filter((opp) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      const matchName = opp.name.toLowerCase().includes(q);
      const matchSponsor = opp.sponsor.toLowerCase().includes(q);
      if (!matchName && !matchSponsor) return false;
    }
    if (charsaddaOnly && !opp.charsadda_flag) return false;
    if (kpOnly && !opp.kp_flag) return false;
    return true;
  });

  // Paginated list
  const totalPages = Math.ceil(filtered.length / itemsPerPage) || 1;
  const paginated = filtered.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="space-y-4">
      {/* Search and Filters Bar */}
      <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search opportunity title, sponsor or keyword..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Categories</option>
              <option value="scholarships">Scholarships</option>
              <option value="internships">Internships</option>
              <option value="financial_aid">Financial Aid</option>
              <option value="research_fellowships">Research & Fellowships</option>
              <option value="competitions_hackathons">Competitions</option>
              <option value="conferences_exchange">Conferences & Exchange</option>
            </select>

            <select
              value={sector}
              onChange={(e) => {
                setSector(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Sectors</option>
              <option value="public">Public University</option>
              <option value="private">Private University</option>
              <option value="both">Both (Public & Private)</option>
            </select>

            <select
              value={semester}
              onChange={(e) => {
                setSemester(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">Semester</option>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                <option key={s} value={s}>
                  Semester {s}
                </option>
              ))}
            </select>

            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Statuses</option>
              <option value="Open">Open</option>
              <option value="Closing soon">Closing Soon (&lt;7d)</option>
              <option value="Rolling / ongoing">Rolling</option>
              <option value="Closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Priority quick toggles */}
        <div className="flex items-center gap-4 pt-1 text-xs text-slate-600 dark:text-slate-400">
          <label className="flex items-center gap-1.5 cursor-pointer hover:text-sky-600">
            <input
              type="checkbox"
              checked={charsaddaOnly}
              onChange={(e) => {
                setCharsaddaOnly(e.target.checked);
                setCurrentPage(1);
              }}
              className="rounded text-sky-600 focus:ring-sky-500"
            />
            Charsadda Reserved / Priority Only
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer hover:text-emerald-600">
            <input
              type="checkbox"
              checked={kpOnly}
              onChange={(e) => {
                setKpOnly(e.target.checked);
                setCurrentPage(1);
              }}
              className="rounded text-emerald-600 focus:ring-emerald-500"
            />
            Khyber Pakhtunkhwa Domicile Favored
          </label>
          <div className="ml-auto text-slate-500">
            Showing {filtered.length} opportunity records
          </div>
        </div>
      </div>

      {/* Main Table / Grid */}
      {isLoading ? (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="h-4 w-48 skeleton"></div>
            <div className="h-4 w-24 skeleton"></div>
          </div>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2">
              <div className="flex justify-between items-center">
                <div className="h-4 w-1/3 skeleton"></div>
                <div className="h-4 w-16 skeleton"></div>
              </div>
              <div className="h-3 w-1/2 skeleton"></div>
              <div className="h-3 w-1/4 skeleton"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="p-8 text-center bg-rose-50 dark:bg-rose-950/30 rounded-2xl border border-rose-200 dark:border-rose-900/50 text-rose-700 dark:text-rose-300">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-rose-500" />
          <p className="font-medium text-xs">{error}</p>
          <button
            onClick={loadOpportunities}
            className="mt-3 px-4 py-1.5 text-xs font-bold bg-rose-600 text-white rounded-xl hover:bg-rose-500 shadow"
          >
            Retry Loading
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm text-slate-500 dark:text-slate-400 space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-2xl mx-auto">
            🔍
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No opportunities match the criteria</h3>
          <p className="text-xs max-w-sm mx-auto">
            Try loosening category or sector filters, clearing keyword search, or resetting semester filters.
          </p>
          <div>
            <button
              onClick={() => {
                setSearch('');
                setCategory('');
                setSector('');
                setSemester('');
                setStatus('');
                setCharsaddaOnly(false);
                setKpOnly(false);
              }}
              className="px-4 py-2 text-xs font-bold bg-sky-500 hover:bg-sky-400 text-white rounded-xl shadow transition-all"
            >
              Reset All Filters
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Opportunity</th>
                  <th className="py-3 px-4">Sector & Semesters</th>
                  <th className="py-3 px-4">Status & Deadline</th>
                  <th className="py-3 px-4">Verification</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60 text-sm">
                {paginated.map((opp) => {
                  const isSaved = savedIds.has(opp.id);
                  const isClosingSoon = opp.status === 'Closing soon' || (opp.days_left !== undefined && opp.days_left <= 7 && opp.days_left >= 0);

                  return (
                    <tr
                      key={opp.id}
                      onClick={() => setSelectedOpp(opp)}
                      className="hover:bg-slate-50/80 dark:hover:bg-slate-750 transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 max-w-sm">
                        <div className="flex items-start gap-2.5">
                          {studentId && (
                            <button
                              type="button"
                              onClick={(e) => toggleBookmark(opp.id, e)}
                              className={`p-1 mt-0.5 rounded hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors ${
                                isSaved ? 'text-amber-500' : 'text-slate-400'
                              }`}
                              title={isSaved ? 'Remove bookmark' : 'Save opportunity'}
                            >
                              <Bookmark className="w-4 h-4" fill={isSaved ? 'currentColor' : 'none'} />
                            </button>
                          )}
                          <div>
                            <div className="font-semibold text-slate-900 dark:text-slate-100 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors line-clamp-1">
                              {opp.name}
                            </div>
                            <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
                              <span>{opp.sponsor}</span>
                              <span>•</span>
                              <span className="capitalize">{opp.category}</span>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-1.5">
                              {opp.charsadda_flag && (
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                                  CHARSADDA PRIORITY
                                </span>
                              )}
                              {opp.kp_flag && (
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                                  KP DOMICILE
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="text-xs">
                          <span className="font-medium text-slate-700 dark:text-slate-300">
                            {opp.university_types === 'both'
                              ? 'Public & Private'
                              : opp.university_types === 'public'
                              ? 'Public Sector'
                              : opp.university_types === 'private'
                              ? 'Private Sector'
                              : 'Not Stated'}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          Semesters: {opp.eligible_semesters && opp.eligible_semesters.length > 0
                            ? opp.eligible_semesters.join(', ')
                            : '1-8'}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                            opp.status === 'Open'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
                              : isClosingSoon
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300'
                              : 'bg-slate-100 text-slate-700 dark:bg-slate-700/60 dark:text-slate-300'
                          }`}
                        >
                          <Clock className="w-3 h-3" />
                          {opp.status} {opp.days_left !== undefined && opp.days_left >= 0 ? `(${opp.days_left}d)` : ''}
                        </span>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          Deadline: {opp.deadline || 'Ongoing'}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                            opp.verification_badge === 'Confirmed' || opp.confirmed_by_official_source
                              ? 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border border-sky-200 dark:border-sky-800/50'
                              : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700'
                          }`}
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          {opp.verification_badge || 'Unverified'} (Tier {opp.source_trust_tier || 1})
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedOpp(opp);
                          }}
                          className="px-3 py-1 text-xs font-medium text-sky-600 dark:text-sky-400 hover:bg-sky-50 dark:hover:bg-sky-950/50 rounded-lg transition-colors border border-sky-200 dark:border-sky-800/40"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900/40 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between text-xs text-slate-500">
            <div>
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                className="p-1.5 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                className="p-1.5 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Slide-over Opportunity Detail Drawer */}
      {selectedOpp && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end animate-fade-in">
          <div className="w-full max-w-xl bg-white dark:bg-slate-800 h-full shadow-2xl border-l border-slate-200 dark:border-slate-700 flex flex-col overflow-y-auto">
            {/* Drawer Header */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-700 flex items-start justify-between bg-slate-50 dark:bg-slate-900/50">
              <div>
                <span className="text-xs font-semibold text-sky-600 dark:text-sky-400 uppercase tracking-wider">
                  {selectedOpp.category}
                </span>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">
                  {selectedOpp.name}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Offered by: {selectedOpp.sponsor} (ID: <code>{selectedOpp.id}</code>)
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedOpp(null)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="p-6 space-y-6 flex-1 text-sm text-slate-700 dark:text-slate-300">
              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300">
                  {selectedOpp.status}
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-100 text-sky-800 dark:bg-sky-950/50 dark:text-sky-300">
                  {selectedOpp.university_types === 'both' ? 'Public & Private' : selectedOpp.university_types}
                </span>
                {selectedOpp.charsadda_flag && (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
                    Charsadda Priority
                  </span>
                )}
                {selectedOpp.kp_flag && (
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-100 text-teal-800 dark:bg-teal-950/50 dark:text-teal-300">
                    KP Favored
                  </span>
                )}
              </div>

              {/* Requirements & Criteria */}
              <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700/60 space-y-2">
                <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Eligibility Criteria
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400">Semesters:</span>{' '}
                    <strong className="text-slate-800 dark:text-slate-200">
                      {selectedOpp.eligible_semesters?.length ? selectedOpp.eligible_semesters.join(', ') : 'All (1-8)'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Degree Levels:</span>{' '}
                    <strong className="text-slate-800 dark:text-slate-200">
                      {selectedOpp.degree_levels || 'Undergraduate'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Discipline:</span>{' '}
                    <strong className="text-slate-800 dark:text-slate-200">
                      {selectedOpp.fields_of_study || 'All Disciplines'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Min CGPA / Marks:</span>{' '}
                    <strong className="text-slate-800 dark:text-slate-200">
                      {selectedOpp.min_gpa_or_marks || 'Not Stated'}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Funding & Benefits */}
              <div className="space-y-1">
                <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Funding Package & Benefits
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {selectedOpp.benefits && selectedOpp.benefits !== 'not stated'
                    ? selectedOpp.benefits
                    : 'Full tuition fee waiver or monthly stipend as specified in official announcement.'}
                </p>
                {selectedOpp.award_amount && (
                  <div className="text-xs font-medium text-emerald-600 dark:text-emerald-400 mt-1">
                    Award Value: {selectedOpp.award_amount}
                  </div>
                )}
              </div>

              {/* Evidence Quote */}
              {selectedOpp.evidence_quote && selectedOpp.evidence_quote !== 'not stated' && (
                <div className="bg-sky-50 dark:bg-sky-950/30 p-3 rounded-lg border border-sky-100 dark:border-sky-900/50 text-xs">
                  <span className="font-semibold text-sky-800 dark:text-sky-300 block mb-1">
                    Verbatim Source Evidence Quote:
                  </span>
                  <p className="italic text-slate-600 dark:text-slate-300">
                    "{selectedOpp.evidence_quote}"
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={handleAddToTracker}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow transition-all"
                >
                  <span>📋</span>
                  <span>Track in Application Kanban</span>
                </button>

                <a
                  href={`/student/prep?opp=${encodeURIComponent(selectedOpp.id)}`}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl shadow transition-all"
                >
                  <span>📝</span>
                  <span>Prepare Application Materials & Checklist</span>
                </a>

                {selectedOpp.official_url && (
                  <a
                    href={selectedOpp.official_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold bg-sky-600 text-white rounded-xl hover:bg-sky-500 transition-colors shadow"
                  >
                    <ExternalLink className="w-4 h-4" /> Open Official Application Portal
                  </a>
                )}
                {selectedOpp.source_url && selectedOpp.source_url !== selectedOpp.official_url && (
                  <a
                    href={selectedOpp.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700/60 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700"
                  >
                    View Announcement Source
                  </a>
                )}
              </div>

            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex justify-between items-center text-xs">
              <span className="text-slate-400">
                Deadline: {selectedOpp.deadline || 'Ongoing'}
              </span>
              <button
                type="button"
                onClick={() => setSelectedOpp(null)}
                className="px-4 py-1.5 font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
