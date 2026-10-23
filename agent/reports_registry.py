"""20 Report Definitions Registry for Student Opportunity Intelligence Platform.
Specifies Report Numbers 01 to 20 across Groups A, B, C, and D with
inclusion rules, query filters, targets, and schedule policies.
"""

from typing import List, Dict, Any
from agent.models import ReportDefinition

REPORT_DEFINITIONS: List[ReportDefinition] = [
    # ---------------- Group A: Scholarships ----------------
    ReportDefinition(
        number="01",
        title="National Scholarships Report",
        category="Scholarships",
        description="Scholarships offered in Pakistan by federal bodies, HEC, provincial programs, public/private universities, and foundations.",
        target_audience="Pakistani students (KP & all provinces) pursuing undergraduate and postgraduate studies",
        filter_criteria={"category": "scholarships", "is_national": True}
    ),
    ReportDefinition(
        number="02",
        title="International Scholarships Report",
        category="Scholarships",
        description="International government scholarships, bilateral awards, and global university funding open to Pakistani applicants (Fulbright, Chevening, DAAD, etc.).",
        target_audience="Students seeking funded Master's, PhD, or international exchange abroad",
        filter_criteria={"category": "scholarships", "is_international": True}
    ),
    ReportDefinition(
        number="03",
        title="Semester-Wise Scholarships Report",
        category="Scholarships",
        description="Scholarship schemes categorized by eligible undergraduate semesters (1-8), continuing student requirements, or graduation stage.",
        target_audience="Undergraduate students seeking semester-targeted or ongoing aid",
        filter_criteria={"category": "scholarships", "has_semester_filter": True}
    ),
    ReportDefinition(
        number="04",
        title="Financial Aid and Fee Support Report",
        category="Scholarships",
        description="Need-based tuition waivers, fee concessions, emergency student grants, and interest-free loans (Qarz-e-Hasna).",
        target_audience="Students with documented financial need across public and private universities",
        filter_criteria={"is_need_based": True}
    ),

    # ---------------- Group B: Internships ----------------
    ReportDefinition(
        number="05",
        title="National Internships Report",
        category="Internships",
        description="Internships in Pakistan across government agencies, technology firms, engineering, banks, NGOs, and research labs.",
        target_audience="University students and fresh graduates in Pakistan seeking industrial experience",
        filter_criteria={"category": "internships", "is_national": True}
    ),
    ReportDefinition(
        number="06",
        title="International Internships Report",
        category="Internships",
        description="Overseas summer research internships, CERN/CERN-open, UN internships, and global placements accepting Pakistani students.",
        target_audience="Advanced students seeking global research and corporate internships abroad",
        filter_criteria={"category": "internships", "is_international": True}
    ),
    ReportDefinition(
        number="07",
        title="Remote and Virtual Internships Report",
        category="Internships",
        description="Online, remote, and virtual internships with flexible working hours and remote stipends.",
        target_audience="Students seeking remote work experience without relocation constraints",
        filter_criteria={"category": "internships", "work_mode": "remote"}
    ),
    ReportDefinition(
        number="08",
        title="Semester-Wise Internships Report",
        category="Internships",
        description="Internships matched for early semesters (Semesters 1-4 for exploration), mid semesters (5-6 for skills), and final-year/recent graduates.",
        target_audience="Students looking for opportunities matching their specific semester standing",
        filter_criteria={"category": "internships", "has_semester_filter": True}
    ),

    # ---------------- Group C: Additional Opportunities ----------------
    ReportDefinition(
        number="09",
        title="Research and Fellowships Report",
        category="Additional Opportunities",
        description="Research assistantships, lab fellowships, undergraduate research grants, and travel fellowships.",
        target_audience="Students pursuing academic research, thesis projects, and scientific inquiries",
        filter_criteria={"category": "research_fellowships"}
    ),
    ReportDefinition(
        number="10",
        title="Competitions and Hackathons Report",
        category="Additional Opportunities",
        description="Coding contests, AI challenges, engineering innovation awards, and national/global hackathons.",
        target_audience="Competitive programmers, innovators, and technology teams",
        filter_criteria={"category": "competitions_hackathons"}
    ),
    ReportDefinition(
        number="11",
        title="Conferences and Student Exchange Report",
        category="Additional Opportunities",
        description="Academic conferences, student exchange semesters (e.g. UGRAD), youth leadership forums, and summit travel grants.",
        target_audience="Students seeking intercultural, academic, and global conference participation",
        filter_criteria={"category": "conferences_exchange"}
    ),
    ReportDefinition(
        number="12",
        title="Jobs and Graduate Programs Report",
        category="Additional Opportunities",
        description="Management trainee programs, entry-level graduate software/engineering roles, and part-time student campus jobs.",
        target_audience="Final-year students and fresh graduates transitioning into the workforce",
        filter_criteria={"category": "jobs_graduate_programs"}
    ),
    ReportDefinition(
        number="13",
        title="Free Learning and Certifications Report",
        category="Additional Opportunities",
        description="Sponsored professional certification vouchers (AWS, Google, Coursera), fully-funded bootcamps, and government skill programs (DigiSkills).",
        target_audience="Students seeking verified industry skills and professional certifications",
        filter_criteria={"category": "free_learning_certifications"}
    ),
    ReportDefinition(
        number="14",
        title="Entrepreneurship and Startup Support Report",
        category="Additional Opportunities",
        description="University incubators (BIC/NIC), student startup seed grants, accelerator cohorts, and business plan competitions.",
        target_audience="Student founders, tech entrepreneurs, and university project commercializers",
        filter_criteria={"category": "entrepreneurship_startups"}
    ),
    ReportDefinition(
        number="15",
        title="Community and Leadership Opportunities Report",
        category="Additional Opportunities",
        description="Youth councils, social impact fellowships, climate activism grants, and NGO community leadership projects.",
        target_audience="Social entrepreneurs, community volunteers, and student leaders",
        filter_criteria={"category": "community_leadership"}
    ),
    ReportDefinition(
        number="16",
        title="Final-Year Project (FYP) Opportunities Report",
        category="Additional Opportunities",
        description="Industry-sponsored capstone topics, Ignite National Grassroots ICT Research Initiative (NGIRI) grants, and mentor matching.",
        target_audience="7th and 8th semester students undertaking final-year degree projects",
        filter_criteria={"category": "fyp_industry_projects"}
    ),

    # ---------------- Group D: Action and Intelligence ----------------
    ReportDefinition(
        number="17",
        title="Upcoming Deadlines Action Report",
        category="Action and Intelligence",
        description="All opportunities closing in 30 days, sorted by urgency: Closing in <= 7 days, <= 15 days, and <= 30 days.",
        target_audience="All students needing urgent application planning before portal closures",
        filter_criteria={"status_in": ["Closing soon", "Open"], "has_deadline": True, "max_days_left": 30}
    ),
    ReportDefinition(
        number="18",
        title="Personalized Student Matches Report",
        category="Action and Intelligence",
        description="Ranked opportunities matching specific student profiles by degree, university sector, semester, CGPA, and district domicile.",
        target_audience="Students seeking personalized shortlists with transparent eligibility reasoning",
        filter_criteria={"is_personalized": True}
    ),
    ReportDefinition(
        number="19",
        title="Application Preparation & Document Checklists Report",
        category="Action and Intelligence",
        description="Actionable checklists for open opportunities: required attested documents, SOP guidelines, recommendation request forms.",
        target_audience="Applicants currently assembling admission and financial aid application packets",
        filter_criteria={"has_application_checklist": True}
    ),
    ReportDefinition(
        number="20",
        title="Verified & Changed Opportunities Intelligence Report",
        category="Action and Intelligence",
        description="Audit log of opportunities verified today, extended deadlines, modified award amounts, new official calls, and flagged fraud alerts.",
        target_audience="University career counselors, financial aid officers, and administrators",
        filter_criteria={"is_change_log": True}
    ),
]


def get_report_definition(report_num: str) -> Optional[ReportDefinition]:
    num_str = str(report_num).strip().zfill(2)
    for r in REPORT_DEFINITIONS:
        if r.number == num_str:
            return r
    return None


def list_report_definitions() -> List[ReportDefinition]:
    return REPORT_DEFINITIONS
