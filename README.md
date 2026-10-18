# Khyber Pakhtunkhwa & Charsadda Daily Scholarship Intelligence Agent

An automated, autonomous AI agent that crawls, verifies, organizes, and reports scholarship, fee-waiver, stipend, grant, and interest-free-loan opportunities available to students with a **Khyber Pakhtunkhwa (KP)** domicile, giving extra weight and dedicated priority to **Charsadda district** domicile holders and key regional universities.

Runs every day at **07:00 Pakistan Standard Time (PKT, UTC+5)** via GitHub Actions, compiles reports across multiple downloadable formats, commits state back to the repository, delivers executive summaries and attachments via Resend, and archives reports as workflow artifacts.

---

## 1. Dual Daily Reports

Every morning, the agent generates two distinct reports separated by university sector:

| Report | Target Audience | Priority Institutions |
| :--- | :--- | :--- |
| **Report A: Public-University Report** | Students enrolled at public-sector universities | **University of Peshawar (UoP)**, **UET Peshawar**, **Bacha Khan University Charsadda (BKUC)**, Islamia College Peshawar (ICP), Khyber Medical University (KMU), The University of Agriculture Peshawar (AUP), Abdul Wali Khan University Mardan (AWKUM), **IMSciences\***, followed by other public universities in Pakistan. |
| **Report B: Private-University Report** | Students enrolled at private-sector universities | **Abasyn University Peshawar**, **CECOS University**, Iqra National University (INU), City University (CUSIT), Sarhad University (SUIT), followed by other private universities in Pakistan. |

*\*Note on IMSciences: The Institute of Management Sciences (IMSciences) Peshawar is an autonomous public-sector institution established by the Government of Khyber Pakhtunkhwa. Per HEC official recognition data, it is classified under the Public Sector.*

### Downloadable Formats for Both Reports
Each report is produced daily into `reports/YYYY-MM-DD/` in 4 formats:
1. **Interactive HTML (`.html`)**: Modern, responsive dashboard with Google Font Inter, priority highlight cards, status badges, expandable detail cards, and `@media print` styling for clean paper printing.
2. **Publication-Ready PDF (`.pdf`)**: Structured vector PDF with dynamic page counts (`NumberedCanvas`), executive KPI tables, priority callout cards, and anti-fraud disclaimers.
3. **Structured Excel (`.xlsx`)**: Multi-sheet workbook (`Active Opportunities`, `Priority Highlights`, `International`, `Watchlist`, `Summary`) with styled dark-navy headers, frozen panes, and color-coded status badges.
4. **Data Science CSV (`.csv`)**: Full tabular export containing all required Section 7 fields formatted with `UTF-8-SIG` encoding for instant compatibility with Microsoft Excel, pandas, and databases.

---

## 2. Scope & Trust Tiers

### In Scope
- **Federal Programmes**: Higher Education Commission (HEC Need-Based, Indigenous, Overseas), Ehsaas / BISP Undergraduate Scholarship Project, Prime Minister's Youth Programme (PMYP), Pakistan Bait-ul-Mal, Federal Ministries.
- **KP Provincial Programmes**: KP Higher Education Department (HED), KP Education Foundation (KPEF), KP Scholarship Portal (KPITB), KP Benevolent Fund, Zakat & Ushr Department (MORA), Auqaf & Minority Affairs, Directorate of Mines & Minerals Labour Welfare, Merged-Districts special quotas.
- **University-Administered Aid**: Merit scholarships, need-based fee waivers, student endowment funds, departmental emergency funds.
- **NGOs, Foundations & Trusts**: Ihsan Trust (Qarz-e-Hasna interest-free student loans), Akhuwat, National Book Foundation (NBF), PEEF national/KP quota awards.
- **Corporate & SOE Schemes**: OGDCL National Talent Hunt, Pakistan Petroleum Limited (PPL), MOL Pakistan (KP operational districts), SNGPL, bank/telecom scholarships.
- **International Programmes**: Chevening (UK), Fulbright (USEFP / US), DAAD (Germany), Commonwealth, Türkiye Bursları, Chinese Government Scholarships (CSC). Formatted in a separate **International** section in each report.

### Excluded
- Programmes strictly limited to other provinces (e.g. Punjab-only, Sindh-only, Balochistan-only) unless KP students are explicitly eligible.
- Expired schemes (except in the *Recently Closed [Last 30 Days]* appendix).
- Unaccountable listings, paid consultancies, or anyone asking for application fees paid to private individuals.

### Source Trust Tiers
- **Tier 1 (Official):** Direct sponsor domains, `*.gov.pk`, `*.edu.pk`, `hec.gov.pk`, `ef.kp.gov.pk`, `scholarships.kpitb.online`. Field status: **Confirmed**.
- **Tier 2 (Official Secondary):** Official partner republishing notices (e.g., UoP SFAO notice about an HEC scheme). Field status: **Via Partner**.
- **Tier 3 (Unofficial):** News aggregators, blogs (e.g. talib.pk). Used **for discovery only**. All fields remain **Unverified** until confirmed by Tier 1 or 2 sources.

---

## 3. Strict Verification & Integrity Rules

- **No Estimation:** Missing values are recorded as exactly `"not stated"`. The agent never guesses amounts, deadlines, GPA cut-offs, or income ceilings.
- **Verbatim Evidence Quotes:** Every record preserves a verbatim excerpt (up to 300 characters) directly copied from the source page.
- **Currency & Cycle Checking:** The call must belong to the active or upcoming cycle (`2026-27`). If the call belongs to a previous cycle, it is marked `Previous cycle – awaiting new call` and placed on the monitoring watch-list.
- **HTTP Link Verification:** Sends HTTP GET requests to `apply_url` and `source_url`. Broken links (4xx/5xx) are flagged in the report summary, never silently dropped.
- **Deduplication:** Fuzzy similarity (ratio &ge; 0.88) or matching application URLs merges duplicates, keeping the most authoritative values and appending all discovered source URLs.
- **Retention Policy:** Records not seen in today's run are marked *not re-confirmed today*. After 30 consecutive days unseen, obsolete records are dropped.

---

## 4. Priority Flags

- `charsadda_flag`: Charsadda named explicitly, scheme covers Peshawar Division / Charsadda zone, or reserved for Bacha Khan University Charsadda.
- `kp_flag`: KP domicile explicitly required or favored, or a KP-wide programme.
- `pakistan_wide_kp_eligible`: Open across Pakistan and KP is not excluded.
- `target_uni_flag`: Names UoP or UET Peshawar (Public Report), or Abasyn University Peshawar (Private Report).
- `merged_districts_only`: Limited to ex-FATA merged districts. *(Charsadda is a settled district of Peshawar Division, NOT a merged district, and never receives this flag).*

---

## 5. Architecture & Code Structure

```
scholorships_agent/
├── .github/
│   └── workflows/
│       └── daily_scholarship_agent.yml    # Daily cron at 02:00 UTC (07:00 PKT)
├── config/
│   ├── settings.yaml                      # Discovery queries, thresholds, watchlist, blocklists
│   ├── sources.yaml                       # Tier 1 & 2 seed URLs across federal, provincial & unis
│   └── universities.json                  # HEC recognised public/private classification (IMSciences=public)
├── data/
│   └── scholarships.json                  # Persistent state across daily runs
├── agent/
│   ├── classifier.py                      # HEC institution sector & priority flag logic
│   ├── deduplicator.py                    # Fuzzy ratio >= 0.88 deduplication & 30-day retention
│   ├── emailer.py                         # Resend API email delivery with attachments & degraded handling
│   ├── fetcher.py                         # HTML & PDF fetcher, anchor link following, clean parsing
│   ├── gemini_client.py                   # Google GenAI client (gemini-3.8-flash + gemini-3.5-flash-lite fallback)
│   ├── models.py                          # Pydantic schemas for Section 7 fields & runtime status
│   ├── normalizer.py                      # Date calculation, status assignment, trust tier, HTTP link checks
│   ├── pipeline.py                        # Full daily orchestrator (Steps 1 to 10)
│   ├── prompts.py                         # System, Discovery, and Extraction prompt templates
│   └── yaml_utils.py                      # Pure-Python YAML configuration loader
├── generators/
│   ├── html_generator.py                  # Responsive HTML dashboard with print CSS
│   ├── pdf_generator.py                   # ReportLab vector PDF generator with NumberedCanvas
│   ├── excel_generator.py                 # Styled multi-sheet openpyxl XLSX generator
│   └── csv_generator.py                   # Standard UTF-8-SIG CSV generator
├── tests/
│   ├── test_classifier.py                 # University classification & priority flag tests
│   ├── test_deduplicator.py               # Fuzzy deduplication & retention tests
│   ├── test_generators.py                 # HTML, PDF, Excel, and CSV generator tests
│   ├── test_normalizer.py                 # Date, status, and trust tier tests
│   └── test_pipeline.py                   # End-to-end pipeline execution test
├── requirements.txt                       # Project dependencies
├── main.py                                # Root entrypoint
└── README.md
```

---

## 6. Local Setup & Quick Start

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/scholorships_agent.git
cd scholorships_agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Agent
```bash
# Run the complete daily pipeline
python main.py run

# Run in test / mock mode (no Gemini API credits consumed)
python main.py run --dry-run

# Run skipping HTTP link checks (for fast offline testing)
python main.py run --dry-run --no-verify-links
```

### Running Test Suite
```bash
pytest tests -v
```

---

## 7. GitHub Actions Daily Automation

The workflow `.github/workflows/daily_scholarship_agent.yml` triggers automatically every day at **02:00 UTC** (07:00 PKT).

### Required GitHub Repository Secrets
To enable live crawling and email delivery in GitHub Actions, navigate to **Settings &rarr; Secrets and variables &rarr; Actions** in your GitHub repository and add:

| Secret Name | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API key (for `gemini-3.8-flash` search grounding and extraction) |
| `RESEND_API_KEY` | Resend API key (e.g. `re_...`) |
| `RESEND_FROM_EMAIL` | Verified sender email in Resend (e.g. `onboarding@resend.dev`) |
| `GMAIL_USER` | Gmail address for sending reports (e.g. `muhammadtalhapro1@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Google 16-character App Password for SMTP authentication |
| `OWNER_EMAIL` | Primary owner recipient email (default: `muhammadtalhapro1@gmail.com`) |
| `FORWARD_EMAIL` | Recipient email address for report forwarding at 07:05 PKT |

---

## 8. Human Review & Configuration Loop

- **Add New Official Portals:** Add the URL and metadata under `sources` in `config/sources.yaml`. No code modifications required.
- **Block Unwanted Domains / Scams:** Add domains to `blocklist_domains` in `config/settings.yaml`.
- **Monitor Recurring Annual Schemes:** Add recurring awards to `watchlist` in `config/settings.yaml` so they permanently appear on the monitoring radar even during off-cycle months.
