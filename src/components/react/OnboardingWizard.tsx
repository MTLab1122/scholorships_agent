import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { auth } from '../../lib/auth';
import { showToast } from './Toast';

export default function OnboardingWizard() {
  const [step, setStep] = useState(1);
  const [user, setUser] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Form State
  const [degreeLevel, setDegreeLevel] = useState('Undergraduate');
  const [university, setUniversity] = useState('University of Peshawar');
  const [universityType, setUniversityType] = useState<'public' | 'private'>('public');
  const [discipline, setDiscipline] = useState('Computer Science');
  const [currentSemester, setCurrentSemester] = useState(4);
  const [cgpa, setCgpa] = useState(3.6);

  const [domicileProvince, setDomicileProvince] = useState('Khyber Pakhtunkhwa');
  const [domicileDistrict, setDomicileDistrict] = useState('Charsadda');
  const [fundingNeed, setFundingNeed] = useState('medium');
  const [workPreference, setWorkPreference] = useState('any');

  const [selectedSkills, setSelectedSkills] = useState<string[]>(['Python', 'Web Development', 'Problem Solving']);
  const [selectedInterests, setSelectedInterests] = useState<string[]>(['Fully Funded Scholarships', 'Tech Internships', 'Research Grants']);

  useEffect(() => {
    const currentUser = auth.getUser();
    if (currentUser) {
      setUser(currentUser);
    }
  }, []);

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  const toggleInterest = (interest: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  };

  const handleFinish = async () => {
    setIsSaving(true);
    try {
      const studentId = user?.student_id || 'STU-1792427107';
      await api.saveStudent({
        id: studentId,
        full_name: user?.full_name || 'Scholar Student',
        email: user?.email || 'student@opportunity.edu.pk',
        university,
        university_type: universityType,
        degree_level: degreeLevel,
        discipline,
        current_semester: currentSemester,
        cgpa,
        domicile_district: domicileDistrict,
        domicile_province: domicileProvince,
        funding_need: fundingNeed,
        work_preference: workPreference,
        skills: selectedSkills,
        interests: selectedInterests
      });

      showToast('Profile configured! Loading personalized matches...', 'success');
      setTimeout(() => {
        window.location.href = '/student/dashboard';
      }, 800);
    } catch (err: any) {
      showToast(err.message || 'Error saving onboarding profile.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const availableSkills = [
    'Python', 'Web Development', 'Problem Solving', 'Data Analysis',
    'Research Writing', 'Machine Learning', 'Communication', 'Graphic Design',
    'Robotics & IoT', 'Database SQL'
  ];

  const availableInterests = [
    'Fully Funded Scholarships', 'Tech Internships', 'Research Grants',
    'HEC Need-Based', 'Erasmus+ & Foreign Exchange', 'Merit Awards',
    'Hackathons & Competitions', 'Women in STEM'
  ];

  return (
    <div className="max-w-3xl mx-auto bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden backdrop-blur-sm animate-fade-in">
      {/* Header Progress Stepper */}
      <div className="bg-gradient-to-r from-sky-900 via-indigo-950 to-slate-900 p-6 text-white border-b border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-sky-400">
              Guided Scholar Onboarding
            </div>
            <h1 className="text-xl font-black tracking-tight mt-0.5">
              Personalize Your Opportunity Intelligence
            </h1>
          </div>
          <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded-full bg-white/10 text-sky-300 border border-white/10">
            Step {step} of 4
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-sky-400 to-indigo-500 transition-all duration-500"
            style={{ width: `${(step / 4) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Wizard Content Body */}
      <div className="p-5 sm:p-8">
        {step === 1 && (
          <div className="space-y-6 animate-fade-in">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Step 1: Academic Standing & Sector
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                The multi-agent system uses your semester and CGPA to unlock exact semester-eligible programs (Semesters 1 to 8+).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Degree Level
                </label>
                <select
                  value={degreeLevel}
                  onChange={(e) => setDegreeLevel(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none"
                >
                  <option value="Undergraduate">Undergraduate (BS / BE / MBBS)</option>
                  <option value="Master's / MPhil">Master&apos;s / MPhil (MS)</option>
                  <option value="PhD">Doctorate (PhD)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  University Sector
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setUniversityType('public')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                      universityType === 'public'
                        ? 'bg-sky-50 dark:bg-sky-950/60 border-sky-500 text-sky-600 dark:text-sky-300'
                        : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    Public Sector
                  </button>
                  <button
                    type="button"
                    onClick={() => setUniversityType('private')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-all ${
                      universityType === 'private'
                        ? 'bg-sky-50 dark:bg-sky-950/60 border-sky-500 text-sky-600 dark:text-sky-300'
                        : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    Private Sector
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Institution Name
                </label>
                <input
                  type="text"
                  value={university}
                  onChange={(e) => setUniversity(e.target.value)}
                  placeholder="e.g. University of Peshawar"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Major / Discipline
                </label>
                <input
                  type="text"
                  value={discipline}
                  onChange={(e) => setDiscipline(e.target.value)}
                  placeholder="e.g. Computer Science"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Current Semester: <span className="text-sky-600 font-bold">{currentSemester}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="8"
                  value={currentSemester}
                  onChange={(e) => setCurrentSemester(Number(e.target.value))}
                  className="w-full accent-sky-500"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                  <span>Semester 1</span>
                  <span>Semester 4</span>
                  <span>Semester 8</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Cumulative GPA: <span className="text-emerald-600 font-bold">{cgpa.toFixed(2)}</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="4.0"
                  value={cgpa}
                  onChange={(e) => setCgpa(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                />
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6 animate-fade-in">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Step 2: Domicile Quotas & Need Level
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Regional quotas (e.g. Charsadda priority, KP, FATA/Merged Districts, Balochistan) give significant advantages for designated funds.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Province of Domicile
                </label>
                <select
                  value={domicileProvince}
                  onChange={(e) => setDomicileProvince(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                >
                  <option value="Khyber Pakhtunkhwa">Khyber Pakhtunkhwa (KP)</option>
                  <option value="Punjab">Punjab</option>
                  <option value="Sindh">Sindh</option>
                  <option value="Balochistan">Balochistan</option>
                  <option value="Gilgit-Baltistan">Gilgit-Baltistan</option>
                  <option value="Azad Jammu & Kashmir">Azad Jammu & Kashmir</option>
                  <option value="Islamabad Capital Territory">Islamabad (ICT)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  District Domicile
                </label>
                <select
                  value={domicileDistrict}
                  onChange={(e) => setDomicileDistrict(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                >
                  <option value="Charsadda">Charsadda (Priority Regional Quota)</option>
                  <option value="Peshawar">Peshawar</option>
                  <option value="Nowshera">Nowshera</option>
                  <option value="Mardan">Mardan</option>
                  <option value="Swat">Swat</option>
                  <option value="Abbottabad">Abbottabad</option>
                  <option value="Kohat">Kohat</option>
                  <option value="Khyber">Khyber (Merged District)</option>
                  <option value="Kurram">Kurram (Merged District)</option>
                  <option value="Other">Other District</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Financial Aid Requirement
                </label>
                <select
                  value={fundingNeed}
                  onChange={(e) => setFundingNeed(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                >
                  <option value="high">High Need (Prioritize 100% Fully Funded Tuition + Stipend)</option>
                  <option value="medium">Medium Need (Tuition waivers + Partial Aid)</option>
                  <option value="merit_only">Merit Based Only (Honor awards & prestigious grants)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Internship Work Preference
                </label>
                <select
                  value={workPreference}
                  onChange={(e) => setWorkPreference(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                >
                  <option value="any">Any (Remote or On-site)</option>
                  <option value="remote">Remote Only</option>
                  <option value="onsite">On-site Only</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6 animate-fade-in">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Step 3: Skills, Strengths & Passions
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Select your core strengths. The Recommendation Agent aligns these with internship position descriptions and grant requirements.
              </p>
            </div>

            <div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Technical & Academic Skills (Click to toggle)
              </div>
              <div className="flex flex-wrap gap-2">
                {availableSkills.map((sk) => {
                  const isSelected = selectedSkills.includes(sk);
                  return (
                    <button
                      key={sk}
                      type="button"
                      onClick={() => toggleSkill(sk)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                        isSelected
                          ? 'bg-sky-500 text-white border-sky-500 shadow-sm'
                          : 'bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-sky-400'
                      }`}
                    >
                      {isSelected ? '✓ ' : '+ '}
                      {sk}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Opportunity Interests & Goals
              </div>
              <div className="flex flex-wrap gap-2">
                {availableInterests.map((it) => {
                  const isSelected = selectedInterests.includes(it);
                  return (
                    <button
                      key={it}
                      type="button"
                      onClick={() => toggleInterest(it)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                        isSelected
                          ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                          : 'bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-indigo-400'
                      }`}
                    >
                      {isSelected ? '★ ' : '+ '}
                      {it}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-6 animate-fade-in text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white flex items-center justify-center text-3xl mx-auto shadow-xl shadow-sky-500/20">
              🚀
            </div>
            <div>
              <h2 className="text-2xl font-black text-slate-900 dark:text-white">
                You&apos;re All Set, Scholar!
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 max-w-md mx-auto">
                We configured your academic profile for <span className="font-bold text-slate-800 dark:text-slate-200">{discipline}</span> at <span className="font-bold text-slate-800 dark:text-slate-200">{university}</span>.
              </p>
            </div>

            {/* Profile Summary Badge */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 max-w-md mx-auto text-left space-y-2 text-xs">
              <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-1.5">
                <span className="text-slate-500">Degree & Semester:</span>
                <span className="font-bold text-slate-900 dark:text-white">{degreeLevel} • Sem {currentSemester}</span>
              </div>
              <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-1.5">
                <span className="text-slate-500">Cumulative GPA:</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">{cgpa.toFixed(2)} / 4.0</span>
              </div>
              <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-1.5">
                <span className="text-slate-500">Quota Domicile:</span>
                <span className="font-bold text-sky-600 dark:text-sky-400">{domicileDistrict}, {domicileProvince}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Matched Sectors:</span>
                <span className="font-bold text-indigo-600 dark:text-indigo-400">{universityType.toUpperCase()} + Cross-Sector</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-400">
              Clicking below will save your preferences and compute your custom recommendations.
            </p>
          </div>
        )}

        {/* Wizard Controls Footer */}
        <div className="mt-8 pt-5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 text-xs font-semibold rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              ← Previous
            </button>
          ) : (
            <div></div>
          )}

          {step < 4 ? (
            <button
              type="button"
              onClick={() => setStep(step + 1)}
              className="px-6 py-2.5 text-xs font-bold rounded-xl bg-sky-500 hover:bg-sky-400 text-white shadow-md shadow-sky-500/20 transition-all flex items-center gap-1.5"
            >
              <span>Next Step</span>
              <span>→</span>
            </button>
          ) : (
            <button
              type="button"
              disabled={isSaving}
              onClick={handleFinish}
              className="px-8 py-3 text-xs font-bold rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-xl shadow-sky-500/25 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  <span>Launching Discovery...</span>
                </>
              ) : (
                <span>Launch My Dashboard 🚀</span>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
