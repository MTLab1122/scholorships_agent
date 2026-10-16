"""Excel (XLSX) Report Generator using openpyxl.
Creates professional multi-sheet workbooks with styled headers, status highlights,
and auto-adjusted columns.
"""

from pathlib import Path
from typing import List, Union
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from agent.models import ScholarshipRecord, ReportSummary


HEADER_FILL = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

STATUS_FILLS = {
    "Closing soon": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),
    "Open": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),
    "Rolling / ongoing": PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid"),
    "Upcoming": PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),
    "Closed": PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"),
}

CHARSADDA_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
CHARSADDA_FONT = Font(name="Calibri", size=10, bold=True, color="B45309")

THIN_BORDER = Border(
    left=Side(style="thin", color="E2E8F0"),
    right=Side(style="thin", color="E2E8F0"),
    top=Side(style="thin", color="E2E8F0"),
    bottom=Side(style="thin", color="E2E8F0"),
)


EXCEL_COLUMNS = [
    ("ID", "id", 14),
    ("Opportunity Name", "name", 35),
    ("Sponsor", "sponsor", 25),
    ("Sponsor Type", "sponsor_type", 16),
    ("Status", "status", 18),
    ("Deadline", "deadline", 14),
    ("Days Left", "days_left", 12),
    ("Charsadda Eligible", "charsadda_flag", 18),
    ("KP Domicile", "kp_flag", 14),
    ("Target Uni", "target_uni_flag", 14),
    ("Award Amount", "award_amount", 30),
    ("Eligible Institutions", "eligible_institutions", 30),
    ("Degree Levels", "degree_levels", 20),
    ("Merit Criteria", "merit_criteria", 25),
    ("Need / Income Cap", "income_cap", 20),
    ("Apply URL", "apply_url", 35),
    ("Verification", "verification_badge", 16),
    ("Source URL", "source_url", 35),
]


class ExcelReportGenerator:
    def __init__(self):
        pass

    def generate_excel(
        self,
        summary: ReportSummary,
        main_records: List[ScholarshipRecord],
        international_records: List[ScholarshipRecord],
        watchlist_records: List[ScholarshipRecord],
        output_path: Union[str, Path]
    ) -> None:
        """Generates formatted multi-tab Excel workbook."""
        wb = openpyxl.Workbook()
        
        # Sheet 1: Active Opportunities
        ws_main = wb.active
        ws_main.title = "Active Opportunities"
        self._populate_sheet(ws_main, main_records)

        # Sheet 2: Priority Highlights
        ws_priority = wb.create_sheet(title="Priority Highlights")
        priority_records = [r for r in main_records if r.charsadda_flag or r.target_uni_flag]
        self._populate_sheet(ws_priority, priority_records)

        # Sheet 3: International Programmes
        ws_intl = wb.create_sheet(title="International")
        self._populate_sheet(ws_intl, international_records)

        # Sheet 4: Watchlist
        ws_watch = wb.create_sheet(title="Watchlist (Awaiting Call)")
        self._populate_sheet(ws_watch, watchlist_records)

        # Sheet 5: Report Summary & Methodology
        ws_sum = wb.create_sheet(title="Report Summary")
        self._populate_summary_sheet(ws_sum, summary)

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)

    def _populate_sheet(self, ws, records: List[ScholarshipRecord]) -> None:
        # Header row
        for col_idx, (title, _, width) in enumerate(EXCEL_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=title)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        ws.row_dimensions[1].height = 28
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(len(EXCEL_COLUMNS))}{max(len(records) + 1, 2)}"

        # Data rows
        for row_idx, r in enumerate(records, start=2):
            rec_dict = r.model_dump()
            ws.row_dimensions[row_idx].height = 20

            for col_idx, (_, field_key, _) in enumerate(EXCEL_COLUMNS, start=1):
                val = rec_dict.get(field_key, "not stated")
                
                # Format booleans nicely
                if isinstance(val, bool):
                    val = "YES" if val else "NO"
                elif val is None:
                    val = "not stated"

                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = Font(name="Calibri", size=10)
                cell.border = THIN_BORDER
                cell.alignment = Alignment(vertical="center")

                # Status highlight
                if field_key == "status" and val in STATUS_FILLS:
                    cell.fill = STATUS_FILLS[val]
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                # Charsadda highlight
                if field_key == "charsadda_flag" and val == "YES":
                    cell.fill = CHARSADDA_FILL
                    cell.font = CHARSADDA_FONT
                    cell.alignment = Alignment(horizontal="center", vertical="center")

    def _populate_summary_sheet(self, ws, summary: ReportSummary) -> None:
        ws.column_dimensions["A"].width = 28
        ws.column_dimensions["B"].width = 45

        ws.cell(row=1, column=1, value="Report Title").font = Font(bold=True)
        ws.cell(row=1, column=2, value=summary.title)

        ws.cell(row=2, column=1, value="Audience").font = Font(bold=True)
        ws.cell(row=2, column=2, value=summary.audience)

        ws.cell(row=3, column=1, value="Last Checked (PKT)").font = Font(bold=True)
        ws.cell(row=3, column=2, value=summary.generated_at_pkt)

        ws.cell(row=4, column=1, value="Run ID").font = Font(bold=True)
        ws.cell(row=4, column=2, value=summary.run_id)

        ws.cell(row=5, column=1, value="Sources Checked").font = Font(bold=True)
        ws.cell(row=5, column=2, value=summary.sources_checked_count)

        ws.cell(row=6, column=1, value="Total Opportunities").font = Font(bold=True)
        ws.cell(row=6, column=2, value=summary.total_opportunities)

        ws.cell(row=7, column=1, value="New Since Yesterday").font = Font(bold=True)
        ws.cell(row=7, column=2, value=summary.new_since_yesterday)

        ws.cell(row=8, column=1, value="Closing in ≤ 7 Days").font = Font(bold=True)
        ws.cell(row=8, column=2, value=summary.closing_within_7_days)

        ws.cell(row=9, column=1, value="Charsadda District Eligible").font = Font(bold=True)
        ws.cell(row=9, column=2, value=summary.charsadda_eligible_count)

        ws.cell(row=10, column=1, value="KP Domicile Eligible").font = Font(bold=True)
        ws.cell(row=10, column=2, value=summary.kp_eligible_count)

        ws.cell(row=11, column=1, value="Broken Links Flagged").font = Font(bold=True)
        ws.cell(row=11, column=2, value=summary.broken_links_count)

        ws.cell(row=12, column=1, value="Degraded Mode Active").font = Font(bold=True)
        ws.cell(row=12, column=2, value="YES" if summary.degraded_mode else "NO")
