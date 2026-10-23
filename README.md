# Student Opportunity Intelligence Platform — Autonomous Multi-Agent System

An enterprise-grade, autonomous multi-agent intelligence platform that crawls, verifies, organizes, matches, and reports academic and career opportunities for students attending public and private universities across Pakistan and worldwide.

The platform provides end-to-end opportunity lifecycle coverage: automated discovery, structured extraction, taxonomy classification, deterministic eligibility verification, official-source authentication, deduplication and change tracking, semester-wise matching (semesters 1–8+), personalized ranking, proactive deadline monitoring, 20 automated publication-grade reports, personalized application preparation packets, and a Kanban application tracker.

It preserves the existing **Khyber Pakhtunkhwa (KP)** and **Charsadda district** daily scholarship intelligence pipeline while expanding coverage to all 20 standardized opportunity categories including national and international internships, fellowships, hackathons, and research grants.

---

## 1. System Architecture & Workflow

The platform operates as a coordinated multi-agent state machine led by a **Master Orchestrator Agent**. Operations requiring deterministic precision (sector matching, semester eligibility, GPA calculations, deduplication hashing, deadline alerts, database mutations) are executed by deterministic code. Large Language Models (Google Gemini) are restricted to unstructured text extraction, taxonomy classification, ambiguous eligibility resolution, and drafting application essays.

```
                          ┌───────────────────────────┐
                          │    Master Orchestrator    │
                          │   (Finite State Machine)  │
                          └─────────────┬─────────────┘
                                        │
    ┌───────────────────────────────────┼───────────────────────────────────┐
    │ Discovery & Ingestion             │ Verification & Matching           │ Publishing & Action
    ▼                                   ▼                                   ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│ 1. Discovery Agent   │    │ 4. Eligibility Agent │    │ 9. Deadline Agent    │
├──────────────────────┤    ├──────────────────────┤    ├──────────────────────┤
│ 2. Extraction Agent  │    │ 5. Source Verifier   │    │ 10. Report Agent     │
├──────────────────────┤    ├──────────────────────┤    ├──────────────────────┤
│ 3. Classifier Agent  │    │ 6. Deduplicator      │    │ 11. App Prep Agent   │
└──────────────────────┘    ├──────────────────────┤    ├──────────────────────┤
                            │ 7. Semester Matcher  │    │ 12. App Tracker      │
                            ├──────────────────────┤    ├──────────────────────┤
                            │ 8. Recommender Agent │    │ 13. Fraud / QC Agent │
                            └──────────────────────┘    ├──────────────────────┤
                                                        │ 14. Coverage Agent   │
                                                        └──────────────────────┘
                                        │
                                        ▼
             ┌─────────────────────────────────────────────────────┐
             │       Central SQLite Database & JSON Store          │
             │   (Opportunities, Profiles, Applications, Audits)   │
             └──────────────────────────┬──────────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
        ┌─────────────────────────┐           ┌─────────────────────────┐
        │   FastAPI Web App UI    │           │  Automated Reports &    │
        │ (Dashboard, Kanban, API)│           │ Email Dispatch (Resend) │
        └─────────────────────────┘           └─────────────────────────┘
```

---

## 2. The 14 Modular Specialized Agents

Each agent is implemented as a standalone, modular component in `agent/agents/`:

| Agent | Module | Responsibility & Guarantees |
| :--- | :--- | :--- |
| **1. Opportunity Discovery** | `discovery_agent.py` | Crawls permitted educational domains (`*.gov.pk`, `*.edu.pk`, university portals, HEC, trusts) and ingests feeds. Respects site terms, rate limits, and access constraints. |
| **2. Opportunity Extraction** | `extraction_agent.py` | Normalizes unstructured announcements into structured Pydantic models. Extracts funding amounts, semesters, GPAs, dates, and verbatim evidence quotes. Never invents missing data. |
| **3. Classification** | `classification_agent.py` | Maps opportunities to 11 standardized taxonomy categories (scholarships, internships, fellowships, hackathons, etc.) and tags geographic/funding attributes. |
| **4. Eligibility Verification** | `eligibility_agent.py` | Performs deterministic rule checking against nationality, degree level, semester range, CGPA cutoffs, and university sectors (public vs. private). |
| **5. Source Verifier** | `source_verifier_agent.py` | Validates domains against trusted whitelist patterns (Tier 1 official, Tier 2 partner, Tier 3 unverified) and tests HTTP link reachability without assuming AI trust. |
| **6. Deduplication & Change Tracking** | `deduplicator_agent.py` | Merges duplicate listings via canonical URL matching and fuzzy title/sponsor similarity (ratio &ge; 0.88). Retains persistent IDs, aggregates source URLs, and records deadline revisions. |
| **7. Semester Matching** | `semester_matching_agent.py` | Evaluates candidates across semesters 1 through 8 and postgraduate stages. Employs discipline synonym mapping, sector verification, and strict criteria scoring. |
| **8. Personalized Recommendation** | `recommendation_agent.py` | Generates explainable match scores (0–100%) for student profiles based on domicile, CGPA, semester, sector, and interests with explicit positive and negative reasoning. |
| **9. Deadline Monitoring** | `deadline_agent.py` | Scans closing dates against configurable notification tiers (30, 15, 7, 3, 1 day) and records alerts idempotently in the database. |
| **10. Report Generation** | `report_agent.py` | Compiles publication-ready files across 4 synchronized formats: PDF (ReportLab vector), Excel (styled openpyxl), CSV (UTF-8-SIG), and Interactive HTML. |
| **11. Application Preparation** | `application_prep_agent.py` | Generates tailored application checklists, document verification guidelines, Statement of Purpose (SOP) essay templates, and recommendation request letters. |
| **12. Application Tracking** | `application_tracker_agent.py` | Manages student application lifecycles across 9 Kanban stages (`interested` &rarr; `applied` &rarr; `awarded`/`rejected`) with strict student data isolation. |
| **13. Fraud & Quality Control** | `fraud_qc_agent.py` | Scans announcements for suspicious fees, non-official payment channels, unrealistic guarantees, broken URLs, and expired listings. |
| **14. Source Coverage & Telemetry** | `source_coverage_agent.py` | Produces administrative telemetry metrics: active sources, verification rates, stale records, duplicate rates, and API usage stats. |

---

## 3. The 20 Standardized Publication Reports

The platform implements a unified report generator supporting 20 separate report definitions:

### Group A — Scholarships
- **Report 01: National Scholarships** — Federal, HEC, provincial, and private foundation scholarships in Pakistan.
- **Report 02: International Scholarships** — Fully funded overseas programs open to Pakistani applicants (Fulbright, Chevening, DAAD, Commonwealth, CSC).
- **Report 03: Semester-Wise Scholarships** — Schemes categorized by eligible semester (1–8) and continuing student criteria.
- **Report 04: Financial Aid and Fee Support** — Need-based tuition waivers, fee concessions, and Qarz-e-Hasna interest-free student loans.

### Group B — Internships
- **Report 05: National Internships** — Domestic placements across technology, banking, government, and industry in Pakistan.
- **Report 06: International Internships** — Overseas summer research programs, CERN, UN, and global internships accepting Pakistani students.
- **Report 07: Remote & Virtual Internships** — Remote technology and research roles with flexible hours and international stipends.
- **Report 08: Semester-Wise Internships** — Placements categorized for early semesters (1–4), intermediate (5–6), and graduating seniors (7–8).

### Group C — Additional Opportunities
- **Report 09: Research and Fellowships** — Lab research assistantships, travel grants, and undergraduate fellowships.
- **Report 10: Competitions and Hackathons** — National and global coding contests, AI hackathons, and innovation awards.
- **Report 11: Conferences and Student Exchange** — Fully funded exchange semesters (e.g., Global UGRAD), youth summits, and travel grants.
- **Report 12: Jobs and Graduate Programs** — Management trainee programs, software engineering roles, and campus employment.
- **Report 13: Free Learning and Certifications** — Sponsored certification vouchers (Google, AWS, Coursera) and government training (DigiSkills).
- **Report 14: Entrepreneurship and Startup Support** — University incubators (BIC/NIC), seed funding, and business pitch competitions.
- **Report 15: Community and Leadership** — Youth councils, social impact initiatives, and leadership development programs.
- **Report 16: Final-Year Project (FYP) Opportunities** — Industry capstones, Ignite NGIRI funding, and industrial mentorship.

### Group D — Action and Intelligence
- **Report 17: Upcoming Deadlines Action Report** — Opportunities closing within 30 days, sorted by urgency.
- **Report 18: Personalized Student Matches** — Ranked opportunities filtered against a student's profile with full eligibility reasoning.
- **Report 19: Application Preparation & Checklists** — Required attested documents, SOP guidelines, and task lists.
- **Report 20: Verified & Changed Opportunities** — Audit intelligence log detailing newly opened, extended, or closed opportunities.

---

## 4. Central Database & Data Model

The persistence layer uses SQLite (`data/opportunities.db`) alongside structured JSON synchronization (`data/scholarships.json`):

- **`opportunities`**: Stores normalized opportunity records, category, sector eligibility, deadline, benefits, and evidence quotes.
- **`sources`**: Registry of authoritative domains, trust tiers, check intervals, and status history.
- **`students`**: User and student profile records (university, sector, semester, CGPA, domicile, interests).
- **`applications`**: Student application tracking records, current status, notes, submission timestamps, and private checklists.
- **`application_tasks`**: Sub-tasks and document deadlines linked to individual applications.
- **`notifications`**: Scheduled and dispatched alerts with unique constraint `(student_id, opportunity_id, alert_type)` preventing duplicate alerts.
- **`generated_reports`**: Historical record of generated files, format paths, record counts, and generation parameters.
- **`agent_logs`**: Execution history, duration, errors, and telemetry metrics.

---

## 5. Dual Daily KP & Charsadda Reports (Preserved Feature)

Every morning at **07:00 PKT**, the original dual-report pipeline executes automatically:

| Report | Target Audience | Priority Institutions |
| :--- | :--- | :--- |
| **Report A: Public-University Report** | Students enrolled at public-sector universities | University of Peshawar (UoP), UET Peshawar, Bacha Khan University Charsadda (BKUC), Islamia College Peshawar (ICP), KMU, AUP, AWKUM, IMSciences. |
| **Report B: Private-University Report** | Students enrolled at private-sector universities | Abasyn University Peshawar, CECOS University, Iqra National University (INU), City University (CUSIT), Sarhad University (SUIT). |

Each report is generated into `reports/YYYY-MM-DD/` in 4 formats: **HTML**, **PDF**, **Excel (XLSX)**, and **CSV**.

---

## 6. Quick Start & Local Development

### Prerequisites
- Python 3.10+
- Virtual Environment (`venv`)

### Installation
```bash
# Clone the repository
git clone https://github.com/MTLab1122/student-opportunity-intelligence.git
cd student-opportunity-intelligence

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
copy .env.example .env
```

---

## 7. CLI Command-Line Reference

The platform features a unified CLI entrypoint:

```bash
# 1. Start the Web Dashboard and REST API Server (http://127.0.0.1:8000)
python main.py server --port 8000

# 2. Run the Full Autonomous Multi-Agent Cycle (Orchestrator)
python main.py orchestrate

# 3. Generate a Specific Report from the 20 Catalog Reports (e.g., Report 01)
python main.py report-20 --report-num 01

# 4. Generate ALL 20 Reports Simultaneously
python main.py report-20 --report-num all

# 5. Run Personalized Matching for a Student Profile
python main.py match --student-id STU-1792427107

# 6. Scan Deadlines and Trigger Idempotent Alerts
python main.py deadlines

# 7. Run the Preserved Daily Scholarship Pipeline
python main.py run

# 8. Run in Dry-Run Mode (Without Consuming AI API Credits)
python main.py run --dry-run --no-verify-links
```

---

## 8. Modern Frontend & Admin Control Center (Astro + Tailwind CSS)

The user interface is built with **Astro 4**, **TypeScript**, **Tailwind CSS**, and **React Islands** for rich interactive elements (Kanban boards, real-time filters, verification queues, report managers).

### Dual Development & Production Modes

1. **Development Mode (with Hot Module Replacement):**
   ```bash
   # Terminal 1: Start Backend API
   python main.py server --port 8000

   # Terminal 2: Start Astro Dev Server (Proxies /api to FastAPI)
   npm run dev
   # Open http://localhost:4321
   ```

2. **Production Mode (Unified FastAPI Server):**
   ```bash
   # Build the production Astro bundle into dist/
   npm run build

   # Start FastAPI server (serves compiled Astro static bundle + REST API)
   python main.py server --port 8000
   # Open http://127.0.0.1:8000
   ```

### Pages Implemented

#### Admin Control Center (`/admin`)
1. `/admin/dashboard` — Live platform KPIs, opportunity distributions, quick actions, recent audits.
2. `/admin/agents` — All 15 specialized agents with live telemetry, statuses, and "Run Now" triggers.
3. `/admin/workflows` — Visual DAG pipeline (Discovery &rarr; Extraction &rarr; Verification &rarr; Matching &rarr; Reports).
4. `/admin/opportunities` — Catalog management with search, sector/semester/Charsadda filters, and slide-in drawer.
5. `/admin/verification` — Review queue with source evidence inspector, quota checks, and approve/flag/reject actions.
6. `/admin/sources` — Official portal directory with live HTTP reachability testing and registration.
7. `/admin/reports` — The 20-category report management center with multi-format downloads (PDF, XLSX, CSV, HTML).
8. `/admin/schedules` — Automation cron schedule management with manual triggers.
9. `/admin/students` — Student directory with academic standings, quota markers, and role permissions.
10. `/admin/health` — System health monitoring (AI providers, SQLite DB, memory, agent workers).
11. `/admin/settings` — Configuration panel for Gemini AI models, default deadlines, and crawling intervals.
12. `/admin/audit-logs` — Immutable audit log ledger of all automated and administrative actions.

#### Student Portal (`/student`)
1. `/student/dashboard` — Personalized student match highlights, upcoming deadlines, and application status cards.
2. `/student/opportunities` — Student opportunity explorer with real-time filters for semester and sector.
3. `/student/recommendations` — Transparent match scoring (0–100%) with positive and negative reasoning.
4. `/student/saved` — Bookmarked opportunities with persistent toggle actions.
5. `/student/applications` — 9-stage interactive Kanban application tracking board (`interested` &rarr; `awarded`).
6. `/student/prep` — Application dossier studio with required document checklists and AI SOP drafts.
7. `/student/profile` — Profile editor syncing GPA, university, degree, semester, skills, and domicile quotas.
8. `/notifications` — Notifications center with unread counters and mark-as-read controls.

### Core REST Endpoints
- `GET /api/health` — System status, total opportunities, and database health.
- `GET /api/opportunities` — Filtered catalog search (by category, sector, semester, search term).
- `GET /api/matches/{student_id}` — Ranked personalized recommendations with explanation strings.
- `GET /api/reports/definitions` — Metadata and filters for all 20 standardized report definitions.
- `POST /api/reports/generate` — On-demand generation of any report definition into PDF, XLSX, CSV, and HTML.
- `GET /api/reports/download` — Secure file download handler.
- `POST /api/orchestrator/run` — Trigger autonomous multi-agent research or matching cycle.
- `GET /api/applications` & `POST /api/applications` — Student Kanban tracking operations.

---

## 9. Testing & Quality Assurance

The codebase includes comprehensive unit, integration, and acceptance tests covering all 20 prompt criteria:

```bash
# Run the complete test suite
pytest -v
```

### Verified Test Matrix (44 Tests, 100% Passing)
- `tests/test_platform_acceptance.py`:
  - `test_criterion_1_existing_scholarship_reports`: Dual daily public/private reports preserved.
  - `test_criterion_2_internship_reports_generation`: National and international internship reports produced.
  - `test_criterion_3_public_private_eligibility`: Public and private sector criteria strictly enforced.
  - `test_criterion_4_semester_filters`: Semester range evaluations (1–8) verified.
  - `test_criterion_5_missing_eligibility_not_matched`: Incomplete criteria flagged as unknown, not auto-matched.
  - `test_criterion_6_expired_opportunities_not_open`: Expired deadlines never shown as open.
  - `test_criterion_7_deduplication_preserves_evidence`: Merged duplicates retain persistent IDs and source URLs.
  - `test_criterion_8_changed_deadline_recorded`: Deadline shifts generate audit log entries.
  - `test_criterion_9_valid_report_files_generated`: PDF, XLSX, CSV, and HTML file structure validated.
  - `test_criterion_10_student_data_isolation`: Cross-student application modifications strictly prohibited.
  - `test_criterion_11_admin_controls_authorization`: Administrative endpoints restricted.
  - `test_criterion_12_failed_jobs_retry_safely`: Retrying failed jobs recovers state without corruption.
  - `test_criterion_13_idempotent_notifications`: Duplicate alert scans produce zero duplicate notifications.
  - `test_criterion_14_unsupported_claims_not_verified`: Unverified sources rejected from verified status.
  - `test_criterion_15_external_source_failures_isolated`: Network/crawl failures do not wipe existing records.
  - `test_criterion_16_empty_search_produces_clean_report`: Empty match queries generate valid empty reports.
  - `test_criterion_17_existing_users_preserved`: DB migrations maintain existing profiles and records.
  - `test_criterion_18_missing_credentials_reported_honestly`: Missing API keys return explicit error states.
  - `test_criterion_19_timezone_boundaries_handled`: UTC/PKT timezone boundaries correctly calculated.
  - `test_criterion_20_mobile_and_desktop_routes`: All frontend templates render cleanly.
- `tests/test_classifier.py`: HEC sector classification and priority flags.
- `tests/test_deduplicator.py`: Fuzzy deduplication and retention window.
- `tests/test_emailer.py`: Email formatting, Resend dispatch, and attachments.
- `tests/test_generators.py`: ReportLab PDF, openpyxl XLSX, CSV, and HTML generators.
- `tests/test_normalizer.py`: Date parsing, HTTP status verification, and evidence extraction.
- `tests/test_pipeline.py`: End-to-end legacy daily scholarship pipeline.

---

## 10. Security & Anti-Fraud Architecture

1. **Deterministic Verification:** An AI model is never allowed to unilaterally mark an opportunity "verified". Verification requires domain whitelist matching (Tier 1/Tier 2) and live HTTP link validation.
2. **Student Privacy Isolation:** Student profiles, saved opportunities, and application records are strictly partitioned. Cross-student data leakage is prevented via parameterized queries and student ID validation.
3. **No Hallucinated Data:** When eligibility details (GPA, semester, funding amount) are missing from source announcements, they are stored as `"not stated"` or `None`. They are never fabricated.
4. **Fraud & Scam Detection:** Scans for illegitimate application fees, individual bank accounts, fake overseas visas, and unverified guarantees. High-risk items are automatically flagged for administrative review.
5. **Zero Secrets in Code:** Credentials for Gemini, Resend, and Gmail are loaded from environment variables. An active `.env` file is excluded via `.gitignore`.

---

## 11. Automation & Deployment

### GitHub Actions (Cloud Automation — PC-Independent)
The workflow `.github/workflows/daily_scholarship_agent.yml` triggers daily at **01:45 UTC (06:45 AM PKT)** via cron. Agents 1–9 process discoveries, verify sources, and monitor deadlines in advance. At exact **07:00:00 AM PKT**, the scheduled gate releases and Agent 10 dispatches the consolidated reports directly to your primary configured email. After each run, updated SQLite (`data/opportunities.db`), JSON state (`data/scholarships.json`), and generated `reports/` are automatically committed and pushed back to the repository.

### Local Execution
- `setup_scheduler.bat`: Unregisters and disables any local Windows Task Scheduler tasks to ensure duplicate emails are never sent when your PC is powered on.
- `run_daily_agent.bat`: Shell runner for manually testing the virtual environment and CLI commands locally.

---

## 12. Troubleshooting & Operational Runbook

| Symptom | Probable Cause | Recommended Resolution |
| :--- | :--- | :--- |
| `APIKeyMissingError` | `GEMINI_API_KEY` is not set in `.env` | Copy `.env.example` to `.env` and provide a valid key from Google AI Studio. |
| Report files empty (0 records) | All active opportunities filtered out by criteria | Verify filter criteria in `agent/reports_registry.py` or inspect DB with `python main.py server`. |
| Port 8000 already in use | Another service is using port 8000 | Run `python main.py server --port 8080`. |
| Rate limited by external website | External portal rate limiting requests | Discovery agent uses exponential backoff; configure `crawl_delay` in `config/settings.yaml`. |
| Email delivery skipped | `RESEND_API_KEY` missing | The platform automatically continues in degraded mode, saving report files locally in `reports/`. |

---

## 13. Production-Ready Frontend & Enterprise Security

The web interface is built with **Astro 4**, **Tailwind CSS**, and **React 18 islands**, providing maximum static rendering speed alongside interactive client applications.

### Key Capabilities & Routes
- **Authentication & RBAC (`/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`):**
  - Real session tokens via `Authorization: Bearer <token>` and `x-auth-token`.
  - Client-side and server-side RBAC guards (`admin` vs `student`) in `src/lib/auth.ts`.
  - Rate limiting handling on auth forms: Displays responsive 60-second countdown upon receiving HTTP 429 Too Many Requests.
  - Quick demo evaluations for both Student (`student@uop.edu.pk`) and Admin (`admin@opportunity.edu.pk`).
  - Irreversible account deletion with name confirmation in `src/components/react/StudentProfileForm.tsx`.
- **Onboarding Wizard (`/onboarding`):**
  - 4-step guided setup: Degree & Semester selection, Regional Quota & Need assessment, Skills & Career Goals, and instantaneous live opportunity preview.
- **Enterprise Disaster Recovery & Backups (`/admin/backups`):**
  - Point-in-time SQLite database backups with one-click creation.
  - Zero-downtime database restoration with automatic pre-restoration emergency snapshots.
  - Live restoration safety guidelines and verification checks.
- **Privacy-Conscious Telemetry (`src/lib/telemetry.ts`):**
  - Anonymous, cookieless event logging without PII.
  - Automatic scrubbing of auth tokens, passwords, and sensitive keys.
  - Global listeners capturing unhandled JavaScript errors and unhandled promise rejections.
- **Accessible UI & Toast System:**
  - Zero intrusive native alerts; replaced with `src/components/react/Toast.tsx` notifications (`success`, `error`, `warning`, `info`).
  - Shimmer skeleton loaders across data tables and lists.
  - Fully responsive mobile drawer navigation and custom 404 page (`/404`).
  - Respects user motion preferences (`prefers-reduced-motion: reduce`).

### Running the Frontend
```bash
# Development mode
npm run dev

# Production build & static validation
npm run build
```
The static site generation pipeline compiles all 33 pages and bundles interactive React components in sub-10 seconds.

