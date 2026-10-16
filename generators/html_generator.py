"""HTML Report Generator for Public and Private university scholarship reports.
Features modern responsive styling, print CSS, priority highlights,
badges, full detail cards, international section, and disclaimer.
"""

import html
import datetime
from typing import List, Dict, Any, Tuple
from agent.models import ScholarshipRecord, ReportSummary


def escape(val: Any) -> str:
    if val is None:
        return "not stated"
    s = str(val).strip()
    return html.escape(s) if s else "not stated"


class HTMLReportGenerator:
    def __init__(self):
        pass

    def generate_report(
        self,
        summary: ReportSummary,
        main_records: List[ScholarshipRecord],
        international_records: List[ScholarshipRecord],
        watchlist_records: List[ScholarshipRecord],
        closed_records: List[ScholarshipRecord],
        unprocessed_sources: List[str],
        report_type: str = "public"
    ) -> str:
        """Renders complete HTML report string."""
        priority_highlights = [r for r in main_records if r.charsadda_flag or r.target_uni_flag]

        audience_desc = (
            "Students currently enrolled or seeking admission at Public-Sector HEC-Recognised Universities "
            "(Priority: University of Peshawar, UET Peshawar, Bacha Khan University Charsadda, ICP, KMU, AUP, AWKUM, IMSciences*)"
            if report_type == "public" else
            "Students currently enrolled or seeking admission at Private-Sector HEC-Recognised Universities "
            "(Priority: Abasyn University Peshawar, CECOS, Iqra National, City University, Sarhad University)"
        )

        html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(summary.title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #0284c7;
      --primary-dark: #0369a1;
      --primary-light: #e0f2fe;
      --accent-charsadda: #b45309;
      --accent-charsadda-bg: #fef3c7;
      --accent-kp: #15803d;
      --accent-kp-bg: #dcfce7;
      --warning: #d97706;
      --warning-bg: #fffbeb;
      --danger: #b91c1c;
      --danger-bg: #fee2e2;
      --bg: #f8fafc;
      --surface: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --border-dark: #cbd5e1;
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 16px;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
      -webkit-font-smoothing: antialiased;
    }}

    .container {{
      max-width: 1320px;
      margin: 0 auto;
    }}

    /* Header styling */
    header.report-header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      color: #ffffff;
      padding: 36px 32px;
      border-radius: var(--radius-lg);
      margin-bottom: 28px;
      box-shadow: var(--shadow-lg);
      position: relative;
      overflow: hidden;
    }}
    header.report-header::after {{
      content: "";
      position: absolute;
      top: -40%;
      right: -10%;
      width: 400px;
      height: 400px;
      background: radial-gradient(circle, rgba(2, 132, 199, 0.25) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 16px;
    }}
    .badge-report-type {{
      background-color: rgba(2, 132, 199, 0.2);
      border: 1px solid rgba(56, 189, 248, 0.4);
      color: #38bdf8;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 4px 12px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      display: inline-block;
      margin-bottom: 8px;
    }}
    h1.report-title {{
      font-size: 2.1rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      line-height: 1.2;
      color: #f8fafc;
    }}
    .audience-tagline {{
      color: #cbd5e1;
      font-size: 0.95rem;
      margin-top: 8px;
      max-width: 900px;
    }}
    .header-meta {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin-top: 20px;
      padding-top: 18px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      font-size: 0.85rem;
      color: #94a3b8;
    }}
    .meta-item strong {{
      color: #f1f5f9;
      font-weight: 600;
    }}

    /* Degraded alert */
    .alert-degraded {{
      background-color: var(--danger-bg);
      border: 1px solid #f87171;
      color: var(--danger);
      padding: 14px 20px;
      border-radius: var(--radius-md);
      margin-bottom: 24px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    /* Summary cards */
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .summary-card {{
      background-color: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 20px;
      box-shadow: var(--shadow-sm);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .summary-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }}
    .summary-card .label {{
      font-size: 0.8rem;
      text-transform: uppercase;
      font-weight: 600;
      color: var(--text-muted);
      letter-spacing: 0.05em;
    }}
    .summary-card .value {{
      font-size: 2rem;
      font-weight: 800;
      color: var(--text);
      margin-top: 4px;
    }}
    .summary-card.highlight-charsadda {{
      border-left: 4px solid var(--accent-charsadda);
    }}
    .summary-card.highlight-charsadda .value {{
      color: var(--accent-charsadda);
    }}
    .summary-card.highlight-closing {{
      border-left: 4px solid var(--warning);
    }}
    .summary-card.highlight-closing .value {{
      color: var(--warning);
    }}

    /* Priority highlights box */
    .priority-box {{
      background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
      border: 1px solid #fde68a;
      border-radius: var(--radius-lg);
      padding: 24px 28px;
      margin-bottom: 32px;
      box-shadow: var(--shadow-sm);
    }}
    .priority-box-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
    }}
    .priority-box-title {{
      font-size: 1.25rem;
      font-weight: 700;
      color: #92400e;
    }}
    .priority-list {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
    }}
    .priority-item-card {{
      background: #ffffff;
      border: 1px solid #fcd34d;
      border-radius: var(--radius-md);
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    /* Section Headings */
    .section-header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-top: 40px;
      margin-bottom: 18px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border);
    }}
    .section-title {{
      font-size: 1.45rem;
      font-weight: 700;
      color: #1e293b;
    }}
    .section-badge {{
      background-color: var(--primary-light);
      color: var(--primary-dark);
      font-size: 0.8rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 9999px;
    }}

    /* Tables */
    .table-wrapper {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      overflow-x: auto;
      box-shadow: var(--shadow-sm);
      margin-bottom: 36px;
    }}
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.9rem;
    }}
    table.data-table th {{
      background-color: #f1f5f9;
      color: #334155;
      font-weight: 700;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }}
    table.data-table td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }}
    table.data-table tr:hover {{
      background-color: #f8fafc;
    }}
    table.data-table tr:last-child td {{
      border-bottom: none;
    }}

    /* Badges */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      white-space: nowrap;
      text-decoration: none;
    }}
    .badge-charsadda {{
      background-color: var(--accent-charsadda-bg);
      color: var(--accent-charsadda);
      border: 1px solid #fde68a;
    }}
    .badge-kp {{
      background-color: var(--accent-kp-bg);
      color: var(--accent-kp);
      border: 1px solid #bbf7d0;
    }}
    .badge-target {{
      background-color: #f3e8ff;
      color: #7e22ce;
      border: 1px solid #e9d5ff;
    }}
    .badge-open {{
      background-color: #dcfce7;
      color: #15803d;
    }}
    .badge-closing-soon {{
      background-color: #fee2e2;
      color: #b91c1c;
      font-weight: 700;
    }}
    .badge-rolling {{
      background-color: #e0f2fe;
      color: #0369a1;
    }}
    .badge-upcoming {{
      background-color: #fef3c7;
      color: #92400e;
    }}
    .badge-closed {{
      background-color: #f1f5f9;
      color: #64748b;
    }}
    .badge-confirmed {{
      background-color: #d1fae5;
      color: #065f46;
      border: 1px solid #a7f3d0;
    }}
    .badge-partner {{
      background-color: #e0e7ff;
      color: #3730a3;
      border: 1px solid #c7d2fe;
    }}
    .badge-unverified {{
      background-color: #fef2f2;
      color: #991b1b;
      border: 1px solid #fecaca;
    }}
    .badge-warning-eligibility {{
      background-color: #fff7ed;
      color: #c2410c;
      border: 1px solid #ffedd5;
      font-size: 0.72rem;
    }}

    /* Buttons */
    .btn-apply {{
      display: inline-block;
      background-color: var(--primary);
      color: #ffffff;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: var(--radius-sm);
      text-decoration: none;
      font-size: 0.82rem;
      transition: background-color 0.15s ease;
      white-space: nowrap;
    }}
    .btn-apply:hover {{
      background-color: var(--primary-dark);
    }}
    .btn-broken {{
      background-color: #cbd5e1;
      color: #475569;
      pointer-events: none;
    }}

    /* Cards */
    .cards-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
      margin-bottom: 36px;
    }}
    .opp-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      box-shadow: var(--shadow-sm);
      transition: border-color 0.15s ease;
    }}
    .opp-card:hover {{
      border-color: var(--border-dark);
    }}
    .opp-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 12px;
    }}
    .opp-title {{
      font-size: 1.2rem;
      font-weight: 700;
      color: #0f172a;
    }}
    .opp-sponsor {{
      color: var(--text-muted);
      font-size: 0.9rem;
      font-weight: 500;
    }}
    .opp-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px 20px;
      margin: 16px 0;
      padding: 16px 0;
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      font-size: 0.875rem;
    }}
    .opp-field strong {{
      color: #334155;
      display: block;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 2px;
    }}
    .evidence-quote {{
      background-color: #f8fafc;
      border-left: 3px solid var(--primary);
      padding: 10px 14px;
      font-size: 0.85rem;
      font-style: italic;
      color: #334155;
      margin: 12px 0;
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    }}

    /* Methodology & Footer */
    footer.report-footer {{
      background-color: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 28px;
      margin-top: 48px;
      font-size: 0.875rem;
      color: #475569;
    }}
    footer h3 {{
      font-size: 1.1rem;
      color: var(--text);
      margin-bottom: 10px;
    }}

    /* Print styles */
    @media print {{
      body {{
        background: #ffffff;
        color: #000000;
        padding: 0;
        font-size: 9pt;
      }}
      header.report-header {{
        background: #f1f5f9;
        color: #0f172a;
        box-shadow: none;
        border: 1px solid #cbd5e1;
        padding: 16px;
        page-break-after: avoid;
      }}
      h1.report-title {{
        color: #0f172a;
        font-size: 1.6rem;
      }}
      .summary-card, .opp-card, .table-wrapper {{
        box-shadow: none;
        border: 1px solid #cbd5e1;
        page-break-inside: avoid;
      }}
      .btn-apply {{
        display: none;
      }}
      .priority-box {{
        background: #fef3c7;
        border: 1px solid #d97706;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header class="report-header" id="reportHeader">
      <div class="header-top">
        <div>
          <span class="badge-report-type">{escape(summary.audience)}</span>
          <h1 class="report-title">{escape(summary.title)}</h1>
          <p class="audience-tagline">{audience_desc}</p>
        </div>
      </div>
      <div class="header-meta">
        <div class="meta-item">Last Checked: <strong>{escape(summary.generated_at_pkt)}</strong></div>
        <div class="meta-item">Run ID: <strong>{escape(summary.run_id)}</strong></div>
        <div class="meta-item">Sources Checked: <strong>{summary.sources_checked_count}</strong></div>
        <div class="meta-item">Opportunities: <strong>{summary.total_opportunities}</strong></div>
      </div>
    </header>

    {"<div class='alert-degraded'><strong>[DEGRADED MODE]</strong> More than 50% of seed sources could not be reached. Opportunities listed below reflect verified active sources and previous verified runs.</div>" if summary.degraded_mode else ""}

    <!-- Summary Metrics -->
    <div class="summary-grid" id="summaryGrid">
      <div class="summary-card">
        <div class="label">Total Opportunities</div>
        <div class="value">{summary.total_opportunities}</div>
      </div>
      <div class="summary-card">
        <div class="label">New Since Yesterday</div>
        <div class="value">{summary.new_since_yesterday}</div>
      </div>
      <div class="summary-card highlight-closing">
        <div class="label">Closing in ≤ 7 Days</div>
        <div class="value">{summary.closing_within_7_days}</div>
      </div>
      <div class="summary-card highlight-charsadda">
        <div class="label">Charsadda Eligible</div>
        <div class="value">{summary.charsadda_eligible_count}</div>
      </div>
      <div class="summary-card">
        <div class="label">KP Eligible</div>
        <div class="value">{summary.kp_eligible_count}</div>
      </div>
      <div class="summary-card">
        <div class="label">Broken Links Flagged</div>
        <div class="value">{summary.broken_links_count}</div>
      </div>
    </div>

    <!-- Priority Highlights Box -->
    <div class="priority-box" id="priorityHighlightsBox">
      <div class="priority-box-header">
        <span style="font-size: 1.4rem;">⭐</span>
        <h2 class="priority-box-title">Priority Highlights (Charsadda District & Target University Opportunities)</h2>
      </div>
      <p style="font-size: 0.9rem; color: #78350f; margin-bottom: 14px;">
        Special weight is given to opportunities specifically mentioning <strong>Charsadda district</strong>, <strong>Bacha Khan University Charsadda (BKUC)</strong>,
        or target institutions (<strong>{"UoP / UET Peshawar" if report_type == "public" else "Abasyn University Peshawar"}</strong>).
      </p>
      <div class="priority-list">
        {self._render_priority_highlight_items(priority_highlights)}
      </div>
    </div>

    <!-- Main Table Section -->
    <div class="section-header">
      <h2 class="section-title">Verified Active Opportunities</h2>
      <span class="section-badge">{len(main_records)} Opportunities</span>
    </div>
    <div class="table-wrapper">
      <table class="data-table" id="mainOpportunitiesTable">
        <thead>
          <tr>
            <th>Opportunity & Sponsor</th>
            <th>Status</th>
            <th>Deadline</th>
            <th>Priority Badges</th>
            <th>Award / Benefits</th>
            <th>Apply Link</th>
            <th>Verification</th>
          </tr>
        </thead>
        <tbody>
          {self._render_table_rows(main_records)}
        </tbody>
      </table>
    </div>

    <!-- Detailed Opportunity Cards -->
    <div class="section-header">
      <h2 class="section-title">Complete Opportunity Details</h2>
      <span class="section-badge">Full Specification Cards</span>
    </div>
    <div class="cards-grid" id="opportunityDetailCards">
      {self._render_detail_cards(main_records)}
    </div>

    <!-- International Section -->
    <div class="section-header">
      <h2 class="section-title">International Programmes (Open to Pakistani & KP Students)</h2>
      <span class="section-badge">{len(international_records)} Programmes</span>
    </div>
    <div class="table-wrapper">
      <table class="data-table" id="internationalTable">
        <thead>
          <tr>
            <th>Opportunity & Sponsor</th>
            <th>Status</th>
            <th>Deadline</th>
            <th>Benefits</th>
            <th>Eligibility</th>
            <th>Action</th>
            <th>Verification</th>
          </tr>
        </thead>
        <tbody>
          {self._render_table_rows(international_records)}
        </tbody>
      </table>
    </div>

    <!-- Watchlist Section -->
    {self._render_watchlist_section(watchlist_records)}

    <!-- Recently Closed Section -->
    {self._render_recently_closed_section(closed_records)}

    <!-- Unprocessed Sources if any -->
    {self._render_unprocessed_sources_section(unprocessed_sources)}

    <!-- Methodology & Disclaimer -->
    <footer class="report-footer" id="methodologyDisclaimer">
      <h3>Methodology & Source Verification Framework</h3>
      <p style="margin-bottom: 12px;">
        This intelligence report is compiled automatically every day at <strong>07:00 Pakistan Standard Time (PKT, UTC+5)</strong>.
        Every listing is verified strictly against official domains:
      </p>
      <ul style="margin-left: 20px; margin-bottom: 14px; line-height: 1.6;">
        <li><strong>Tier 1 (Official):</strong> Direct government domains (<code>*.gov.pk</code>, <code>hec.gov.pk</code>, <code>ef.kp.gov.pk</code>, <code>scholarships.kpitb.online</code>), university domains (<code>*.edu.pk</code>), and accountable sponsor platforms. Marked with a green <em>Confirmed</em> badge.</li>
        <li><strong>Tier 2 (Official Secondary):</strong> Partner republishing notices (e.g. university SFAO notice on federal schemes). Marked <em>Via Partner</em>.</li>
        <li><strong>Tier 3 (Unofficial):</strong> Aggregators and press announcements. Used for discovery only; retained as <em>Unverified</em> until confirmed on official domains.</li>
      </ul>
      <p style="color: #64748b; font-size: 0.82rem; margin-top: 12px;">
        <strong>Important Disclaimer:</strong> While automated verification checks apply links, deadlines, and verbatim eligibility requirements daily,
        students are strongly advised to consult the respective university Students Financial Aid Office (SFAO) or sponsor portal to confirm exact document submission and attestation procedures before applying.
      </p>
    </footer>
  </div>
</body>
</html>
"""
        return html_out

    def _render_priority_highlight_items(self, highlights: List[ScholarshipRecord]) -> str:
        if not highlights:
            return "<p style='color: #78350f;'>No specific Charsadda or target-university priority items closing in this period.</p>"
        
        items_html = []
        for r in highlights[:6]:
            badge_list = []
            if r.charsadda_flag:
                badge_list.append("<span class='badge badge-charsadda'>Charsadda Priority</span>")
            if r.target_uni_flag:
                badge_list.append("<span class='badge badge-target'>Target Institution</span>")
            
            items_html.append(f"""
            <div class="priority-item-card">
              <div>
                <div style="display: flex; gap: 6px; margin-bottom: 6px;">{" ".join(badge_list)}</div>
                <h4 style="font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 4px;">{escape(r.name)}</h4>
                <p style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">{escape(r.sponsor)}</p>
                <p style="font-size: 0.82rem; color: #334155;"><strong>Award:</strong> {escape(r.award_amount)}</p>
              </div>
              <div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.8rem; font-weight: 600; color: #b45309;">Deadline: {escape(r.deadline)}</span>
                {self._render_apply_link(r)}
              </div>
            </div>
            """)
        return "\n".join(items_html)

    def _render_table_rows(self, records: List[ScholarshipRecord]) -> str:
        if not records:
            return "<tr><td colspan='7' style='text-align:center; padding: 24px; color: #64748b;'>No opportunities recorded in this category.</td></tr>"

        rows = []
        for r in records:
            status_badge = self._get_status_badge(r.status, r.days_left)
            verification_badge = self._get_verification_badge(r.verification_badge)
            flags_html = self._get_flags_badges(r)
            warning_html = "<span class='badge badge-warning-eligibility'>Confirm Uni Sector</span>" if r.university_types == "not stated" else ""

            rows.append(f"""
            <tr>
              <td>
                <div style="font-weight: 600; color: #0f172a;">{escape(r.name)}</div>
                <div style="font-size: 0.8rem; color: #64748b;">{escape(r.sponsor)}</div>
                {warning_html}
              </td>
              <td>{status_badge}</td>
              <td style="white-space: nowrap; font-size: 0.85rem; font-weight: 500;">
                {escape(r.deadline)}
                {f"<div style='font-size: 0.75rem; color: #b91c1c;'>({r.days_left}d left)</div>" if r.days_left is not None and 0 <= r.days_left <= 7 else ""}
              </td>
              <td><div style="display: flex; flex-direction: column; gap: 4px;">{flags_html}</div></td>
              <td style="font-size: 0.82rem; max-width: 250px;">{escape(r.award_amount)}</td>
              <td>{self._render_apply_link(r)}</td>
              <td>{verification_badge}</td>
            </tr>
            """)
        return "\n".join(rows)

    def _render_detail_cards(self, records: List[ScholarshipRecord]) -> str:
        if not records:
            return "<p style='color: #64748b; padding: 16px;'>No detail cards to display.</p>"

        cards = []
        for r in records:
            flags = self._get_flags_badges(r)
            status_badge = self._get_status_badge(r.status, r.days_left)
            ver_badge = self._get_verification_badge(r.verification_badge)
            apply_btn = self._render_apply_link(r)

            cards.append(f"""
            <div class="opp-card" id="{escape(r.id)}">
              <div class="opp-card-header">
                <div>
                  <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px;">
                    {flags}
                    {status_badge}
                    {ver_badge}
                  </div>
                  <h3 class="opp-title">{escape(r.name)}</h3>
                  <div class="opp-sponsor">Sponsor: <strong>{escape(r.sponsor)}</strong> ({escape(r.sponsor_type)})</div>
                </div>
                <div>{apply_btn}</div>
              </div>

              <div class="opp-grid">
                <div class="opp-field"><strong>Eligible Universities:</strong> {escape(r.eligible_institutions)} ({escape(r.university_types)})</div>
                <div class="opp-field"><strong>Degree Levels:</strong> {escape(r.degree_levels)}</div>
                <div class="opp-field"><strong>Fields of Study:</strong> {escape(r.fields_of_study)}</div>
                <div class="opp-field"><strong>Academic Years:</strong> {escape(r.academic_years)}</div>
                <div class="opp-field"><strong>Domicile Requirements:</strong> {escape(r.domicile_requirements)}</div>
                <div class="opp-field"><strong>District / Tehsil:</strong> {escape(r.district_requirements)} ({escape(r.other_geographic)})</div>
                <div class="opp-field"><strong>KP / Charsadda Eligibility:</strong> KP: {escape(r.kp_eligibility)} | Charsadda: {escape(r.charsadda_eligibility)}</div>
                <div class="opp-field"><strong>Academic Threshold:</strong> {escape(r.min_gpa_or_marks)}</div>
                <div class="opp-field"><strong>Family Income Cap:</strong> {escape(r.income_cap)}</div>
                <div class="opp-field"><strong>Need Criteria:</strong> {escape(r.need_criteria)}</div>
                <div class="opp-field"><strong>Merit Criteria:</strong> {escape(r.merit_criteria)}</div>
                <div class="opp-field"><strong>Gender / Age Limit:</strong> Gender: {escape(r.gender)} | Age: {escape(r.age_limit)}</div>
                <div class="opp-field"><strong>Award Amount:</strong> {escape(r.award_amount)}</div>
                <div class="opp-field"><strong>Benefits:</strong> {escape(r.benefits)}</div>
                <div class="opp-field"><strong>Duration & Awards:</strong> Duration: {escape(r.duration)} | Slots: {escape(r.number_of_awards)}</div>
                <div class="opp-field"><strong>Application Procedure:</strong> {escape(r.application_procedure)}</div>
                <div class="opp-field"><strong>Required Documents:</strong> {escape(r.required_documents)}</div>
                <div class="opp-field"><strong>Attestation Rules:</strong> {escape(r.attestation_requirements)}</div>
                <div class="opp-field"><strong>Important Dates:</strong> Open: {escape(r.opening_date)} | Deadline: {escape(r.deadline)} | Hardcopy: {escape(r.document_upload_deadline)}</div>
                <div class="opp-field"><strong>Cycle & Contact:</strong> Cycle: {escape(r.cycle)} | Email: {escape(r.contact_email)} | Tel: {escape(r.contact_phone)}</div>
              </div>

              {"<div class='evidence-quote'><strong>Verbatim Official Quote:</strong> &ldquo;" + escape(r.evidence_quote) + "&rdquo;</div>" if r.evidence_quote != "not stated" else ""}

              <div style="font-size: 0.8rem; color: #64748b; margin-top: 10px; display: flex; justify-content: space-between; flex-wrap: wrap;">
                <div>First Seen: <strong>{escape(r.first_seen)}</strong> | Last Verified: <strong>{escape(r.last_verified)}</strong></div>
                <div>Source: <a href="{escape(r.source_url)}" target="_blank" rel="noopener" style="color: var(--primary);">{escape(r.source_url[:60])}...</a></div>
              </div>
            </div>
            """)
        return "\n".join(cards)

    def _render_watchlist_section(self, watchlist: List[ScholarshipRecord]) -> str:
        if not watchlist:
            return ""
        return f"""
        <div class="section-header">
          <h2 class="section-title">Previous Cycle / Awaiting New Call (Watch-list)</h2>
          <span class="section-badge">{len(watchlist)} Monitored</span>
        </div>
        <p style="color: #64748b; font-size: 0.88rem; margin-bottom: 14px;">
          These are established recurring schemes currently between cycles. The agent monitors these daily for opening announcements for the upcoming academic cycle.
        </p>
        <div class="table-wrapper">
          <table class="data-table" id="watchlistTable">
            <thead>
              <tr>
                <th>Scheme Name</th>
                <th>Sponsor</th>
                <th>Last Known Cycle</th>
                <th>Monitoring Status</th>
                <th>Official Portal</th>
              </tr>
            </thead>
            <tbody>
              {self._render_watchlist_rows(watchlist)}
            </tbody>
          </table>
        </div>
        """

    def _render_watchlist_rows(self, watchlist: List[ScholarshipRecord]) -> str:
        rows = []
        for r in watchlist:
            rows.append(f"""
            <tr>
              <td><strong>{escape(r.name)}</strong></td>
              <td>{escape(r.sponsor)}</td>
              <td>{escape(r.cycle)}</td>
              <td><span class="badge badge-upcoming">Awaiting New Call</span></td>
              <td><a href="{escape(r.apply_url if r.apply_url != 'not stated' else r.source_url)}" target="_blank" class="btn-apply" style="padding: 4px 10px; font-size: 0.75rem;">Check Portal</a></td>
            </tr>
            """)
        return "\n".join(rows)

    def _render_recently_closed_section(self, closed_records: List[ScholarshipRecord]) -> str:
        if not closed_records:
            return ""
        return f"""
        <div class="section-header">
          <h2 class="section-title">Recently Closed Opportunities (Last 30 Days)</h2>
          <span class="section-badge">{len(closed_records)} Closed</span>
        </div>
        <div class="table-wrapper">
          <table class="data-table" id="recentlyClosedTable">
            <thead>
              <tr>
                <th>Opportunity</th>
                <th>Sponsor</th>
                <th>Closed On</th>
                <th>Status</th>
                <th>Record Archive</th>
              </tr>
            </thead>
            <tbody>
              {"".join([f"<tr><td>{escape(r.name)}</td><td>{escape(r.sponsor)}</td><td>{escape(r.deadline)}</td><td><span class='badge badge-closed'>Closed</span></td><td><a href='{escape(r.source_url)}' target='_blank' style='color: var(--primary); font-size: 0.8rem;'>Archive Notice</a></td></tr>" for r in closed_records])}
            </tbody>
          </table>
        </div>
        """

    def _render_unprocessed_sources_section(self, unprocessed: List[str]) -> str:
        if not unprocessed:
            return ""
        items = "".join([f"<li style='margin-bottom: 4px;'><code style='color: #b91c1c;'>{escape(u)}</code></li>" for u in unprocessed])
        return f"""
        <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-radius: var(--radius-md); padding: 18px 24px; margin-bottom: 32px;">
          <h4 style="color: #991b1b; font-size: 0.95rem; margin-bottom: 8px;">Sources That Could Not Be Processed Today:</h4>
          <ul style="font-size: 0.85rem; margin-left: 20px;">{items}</ul>
        </div>
        """

    def _render_apply_link(self, r: ScholarshipRecord) -> str:
        if r.apply_url and r.apply_url != "not stated" and r.apply_url.startswith("http"):
            if r.link_status_apply == "broken":
                return f'<a href="{escape(r.apply_url)}" target="_blank" rel="noopener" class="btn-apply btn-broken" title="Link returned 4xx/5xx error">Broken Link Flagged</a>'
            elif r.link_status_apply == "unreachable":
                return f'<a href="{escape(r.apply_url)}" target="_blank" rel="noopener" class="btn-apply btn-broken" title="Portal timed out or connection refused">Unreachable Link</a>'
            else:
                return f'<a href="{escape(r.apply_url)}" target="_blank" rel="noopener" class="btn-apply">Apply Online &rarr;</a>'
        elif r.source_url and r.source_url != "not stated" and r.source_url.startswith("http"):
            return f'<a href="{escape(r.source_url)}" target="_blank" rel="noopener" class="btn-apply">View Notice &rarr;</a>'
        return '<span style="font-size: 0.8rem; color: #94a3b8;">not stated</span>'

    def _get_status_badge(self, status: str, days_left: Any) -> str:
        if status == "Closing soon":
            return f'<span class="badge badge-closing-soon">Closing soon ({days_left}d)</span>'
        elif status == "Open":
            return f'<span class="badge badge-open">Open</span>'
        elif status == "Upcoming":
            return f'<span class="badge badge-upcoming">Upcoming</span>'
        elif status == "Rolling / ongoing":
            return f'<span class="badge badge-rolling">Rolling / ongoing</span>'
        elif status == "Closed":
            return f'<span class="badge badge-closed">Closed</span>'
        return f'<span class="badge badge-rolling">{escape(status)}</span>'

    def _get_verification_badge(self, badge: str) -> str:
        if badge == "Confirmed":
            return '<span class="badge badge-confirmed">Confirmed (Tier 1)</span>'
        elif badge == "Via Partner":
            return '<span class="badge badge-partner">Via Partner (Tier 2)</span>'
        return '<span class="badge badge-unverified">Unverified (Tier 3)</span>'

    def _get_flags_badges(self, r: ScholarshipRecord) -> str:
        badges = []
        if r.charsadda_flag:
            badges.append('<span class="badge badge-charsadda">Charsadda Priority</span>')
        if r.kp_flag:
            badges.append('<span class="badge badge-kp">KP Domicile</span>')
        if r.target_uni_flag:
            badges.append('<span class="badge badge-target">Target Uni</span>')
        return " ".join(badges) or "<span style='color: #94a3b8; font-size: 0.75rem;'>General</span>"
