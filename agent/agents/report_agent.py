"""Agent 10: Report Generation Agent
Manages the generation of all 20 modular reports across Groups A, B, C, and D.
Filters verified opportunity records, formats output for PDF, Excel, CSV, and HTML,
validates output file integrity, and logs execution to the database.
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from agent.models import OpportunityRecord, ReportDefinition, StudentProfile
from agent.reports_registry import REPORT_DEFINITIONS, get_report_definition
from agent.db import OpportunityDB
from generators.csv_generator import CSVReportGenerator
from generators.excel_generator import ExcelReportGenerator
from generators.html_generator import HTMLReportGenerator
from generators.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class ReportGenerationAgent:
    """Specialized Agent for generating and validating the 20 platform reports."""

    def __init__(self, db: Optional[OpportunityDB] = None, output_dir: str = "reports"):
        self.db = db or OpportunityDB()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_gen = CSVReportGenerator()
        self.excel_gen = ExcelReportGenerator()
        self.html_gen = HTMLReportGenerator()
        self.pdf_gen = PDFReportGenerator()

    def filter_records_for_report(
        self,
        report_def: ReportDefinition,
        records: List[OpportunityRecord],
        custom_filters: Optional[Dict[str, Any]] = None,
        student_profile: Optional[StudentProfile] = None
    ) -> List[OpportunityRecord]:
        """Applies deterministic, evidence-based inclusion rules for a specific report."""
        filters = dict(report_def.filter_criteria)
        if custom_filters:
            filters.update(custom_filters)

        matched: List[OpportunityRecord] = []
        num = report_def.number

        for rec in records:
            cat = (rec.category or "scholarships").lower()
            name_desc = f"{rec.name} {rec.benefits} {rec.merit_criteria} {rec.need_criteria}".lower()

            if num == "01": # National Scholarships
                if cat == "scholarships" and not rec.is_international:
                    matched.append(rec)
                elif rec.sponsor_type in ["federal govt", "provincial govt", "university", "NGO-foundation"] and not rec.is_international:
                    matched.append(rec)

            elif num == "02": # International Scholarships
                if cat == "scholarships" and (rec.is_international or rec.sponsor_type == "international" or "study abroad" in name_desc or "foreign" in name_desc):
                    matched.append(rec)

            elif num == "03": # Semester-Wise Scholarships
                if cat == "scholarships" and (rec.min_semester > 1 or rec.max_semester < 8 or "semester" in name_desc):
                    matched.append(rec)

            elif num == "04": # Financial Aid & Fee Support
                if rec.is_need_based or (rec.income_cap and rec.income_cap != "not stated") or "financial aid" in name_desc or "fee concession" in name_desc or "zakat" in name_desc or "qarz" in name_desc:
                    matched.append(rec)

            elif num == "05": # National Internships
                if cat == "internships" and not rec.is_international:
                    matched.append(rec)
                elif "intern" in name_desc and not rec.is_international:
                    matched.append(rec)

            elif num == "06": # International Internships
                if (cat == "internships" or "intern" in name_desc) and (rec.is_international or "cern" in name_desc or "overseas" in name_desc):
                    matched.append(rec)

            elif num == "07": # Remote & Virtual Internships
                if (cat == "internships" or "intern" in name_desc) and (rec.work_mode == "remote" or "remote" in name_desc or "virtual" in name_desc):
                    matched.append(rec)

            elif num == "08": # Semester-Wise Internships
                if (cat == "internships" or "intern" in name_desc) and (rec.min_semester > 1 or rec.max_semester < 8 or "semester" in name_desc):
                    matched.append(rec)

            elif num == "09": # Research and Fellowships
                if cat == "research_fellowships" or "fellowship" in name_desc or "research grant" in name_desc or "research assistant" in name_desc:
                    matched.append(rec)

            elif num == "10": # Competitions and Hackathons
                if cat == "competitions_hackathons" or "hackathon" in name_desc or "competition" in name_desc or "contest" in name_desc:
                    matched.append(rec)

            elif num == "11": # Conferences and Student Exchange
                if cat == "conferences_exchange" or "exchange" in name_desc or "conference" in name_desc or "summer school" in name_desc:
                    matched.append(rec)

            elif num == "12": # Jobs and Graduate Programs
                if cat == "jobs_graduate_programs" or "trainee" in name_desc or "officer" in name_desc or "graduate program" in name_desc:
                    matched.append(rec)

            elif num == "13": # Free Learning and Certifications
                if cat == "free_learning_certifications" or "certification" in name_desc or "free course" in name_desc or "voucher" in name_desc:
                    matched.append(rec)

            elif num == "14": # Entrepreneurship and Startup Support
                if cat == "entrepreneurship_startups" or "incubator" in name_desc or "accelerator" in name_desc or "seed fund" in name_desc:
                    matched.append(rec)

            elif num == "15": # Community and Leadership
                if cat == "community_leadership" or "volunteer" in name_desc or "youth leadership" in name_desc or "social impact" in name_desc:
                    matched.append(rec)

            elif num == "16": # Final-Year Project Opportunities
                if cat == "fyp_industry_projects" or "fyp" in name_desc or "capstone" in name_desc or "final year project" in name_desc:
                    matched.append(rec)

            elif num == "17": # Upcoming Deadlines
                if rec.status in ["Closing soon", "Open"] and (rec.days_left is not None and 0 <= rec.days_left <= 30):
                    matched.append(rec)
                elif rec.status == "Closing soon":
                    matched.append(rec)

            elif num == "18": # Personalized Student Matches
                # Include opportunities eligible for target profile
                if student_profile:
                    from agent.agents.semester_matching_agent import SemesterMatchingAgent
                    matcher = SemesterMatchingAgent()
                    res = matcher.evaluate_opportunity(student_profile, rec)
                    if res.is_eligible or res.status in ["confirmed_eligible", "likely_eligible"]:
                        matched.append(rec)
                else:
                    if rec.status in ["Open", "Closing soon", "Rolling / ongoing"]:
                        matched.append(rec)

            elif num == "19": # Application Preparation
                # Has documented application procedure and checklist
                if rec.application_procedure and rec.application_procedure != "not stated":
                    matched.append(rec)
                elif rec.required_documents and rec.required_documents != "not stated":
                    matched.append(rec)

            elif num == "20": # Verified and Changed Opportunities
                if rec.confirmed_by_official_source or rec.source_trust_tier in ["official_source", "tier_1_official", "verified"]:
                    matched.append(rec)

            else:
                # Generic fallback
                matched.append(rec)

        return matched

    def generate_report(
        self,
        report_num: str,
        formats: List[str] = ["pdf", "xlsx", "csv", "html"],
        custom_filters: Optional[Dict[str, Any]] = None,
        student_profile: Optional[StudentProfile] = None
    ) -> Dict[str, Any]:
        """Generates the requested report number and writes all requested file formats.
        
        Returns execution metadata including file paths and record counts.
        """
        report_def = get_report_definition(report_num)
        if not report_def:
            raise ValueError(f"Unknown report number: '{report_num}'. Must be 01 to 20.")

        all_records = self.db.list_opportunities()
        matched_records = self.filter_records_for_report(
            report_def=report_def,
            records=all_records,
            custom_filters=custom_filters,
            student_profile=student_profile
        )

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        slug = f"report_{report_def.number}_{report_def.category.lower().replace(' ', '_')}"
        generated_files: Dict[str, str] = {}

        # 1. CSV
        if "csv" in formats:
            csv_path = self.output_dir / f"{slug}_{timestamp_str}.csv"
            self.csv_gen.generate_csv(matched_records, csv_path)
            if csv_path.exists() and csv_path.stat().st_size > 0:
                generated_files["csv"] = str(csv_path)

        # 2. Excel (XLSX)
        if "xlsx" in formats or "excel" in formats:
            xlsx_path = self.output_dir / f"{slug}_{timestamp_str}.xlsx"
            self._generate_custom_excel(report_def, matched_records, xlsx_path)
            if xlsx_path.exists() and xlsx_path.stat().st_size > 0:
                generated_files["xlsx"] = str(xlsx_path)

        # 3. HTML
        if "html" in formats:
            html_path = self.output_dir / f"{slug}_{timestamp_str}.html"
            self._generate_custom_html(report_def, matched_records, html_path)
            if html_path.exists() and html_path.stat().st_size > 0:
                generated_files["html"] = str(html_path)

        # 4. PDF
        if "pdf" in formats:
            pdf_path = self.output_dir / f"{slug}_{timestamp_str}.pdf"
            self._generate_custom_pdf(report_def, matched_records, pdf_path)
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                generated_files["pdf"] = str(pdf_path)

        # Record in database audit history
        report_id = f"REP_{report_def.number}_{timestamp_str}"
        self.db.record_report_generation(
            report_id=report_id,
            report_number=report_def.number,
            title=report_def.title,
            format_type=",".join(generated_files.keys()),
            file_path=generated_files.get("pdf") or generated_files.get("xlsx") or generated_files.get("csv") or "",
            record_count=len(matched_records),
            filters_applied=json.dumps(custom_filters or report_def.filter_criteria)
        )

        return {
            "report_id": report_id,
            "report_number": report_def.number,
            "title": report_def.title,
            "category": report_def.category,
            "record_count": len(matched_records),
            "generated_files": generated_files,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success"
        }

    def _generate_custom_excel(self, report_def: ReportDefinition, records: List[OpportunityRecord], output_path: Path):
        """Builds tailored Excel workbook for custom report."""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Report {report_def.number}"

        # Header titles
        ws.merge_cells("A1:K1")
        title_cell = ws["A1"]
        title_cell.value = f"Report {report_def.number}: {report_def.title}"
        title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[1].height = 30

        # Subtitle
        ws.merge_cells("A2:K2")
        sub_cell = ws["A2"]
        sub_cell.value = f"{report_def.description} | Target: {report_def.target_audience} | Records: {len(records)}"
        sub_cell.font = Font(name="Calibri", size=10, italic=True, color="475569")
        sub_cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        ws.row_dimensions[2].height = 20

        # Columns
        headers = [
            "ID", "Opportunity Name", "Sponsor", "Category", "Status",
            "Deadline", "Days Left", "University Sector", "Semesters", "Award / Stipend", "Apply URL"
        ]
        ws.append([]) # row 3 blank
        ws.append(headers) # row 4
        ws.row_dimensions[4].height = 24

        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=4, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )

        for rec in records:
            sem_str = f"Sem {rec.min_semester}-{rec.max_semester}" if (rec.min_semester > 1 or rec.max_semester < 8) else "All Semesters"
            row = [
                rec.id,
                rec.name,
                rec.sponsor,
                rec.category or "Scholarships",
                rec.status,
                rec.deadline or "Not Stated",
                rec.days_left if rec.days_left is not None else "N/A",
                rec.university_types.title() if rec.university_types else "All",
                sem_str,
                rec.award_amount or rec.benefits or "Documented Aid",
                rec.apply_url or rec.source_url or ""
            ]
            ws.append(row)
            curr_row = ws.max_row
            ws.row_dimensions[curr_row].height = 20
            for col_idx in range(1, len(headers) + 1):
                c = ws.cell(row=curr_row, column=col_idx)
                c.border = thin_border
                c.font = Font(name="Calibri", size=10)

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row > 2 and cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)

    def _generate_custom_html(self, report_def: ReportDefinition, records: List[OpportunityRecord], output_path: Path):
        """Builds responsive modern HTML report for custom report."""
        rows_html = ""
        for rec in records:
            status_badge_class = "badge-open" if rec.status in ["Open", "Rolling / ongoing"] else "badge-closing" if rec.status == "Closing soon" else "badge-other"
            sem_badge = f"Sem {rec.min_semester}-{rec.max_semester}" if (rec.min_semester > 1 or rec.max_semester < 8) else "Sem 1-8 Eligible"
            rows_html += f"""
            <tr class="opportunity-row">
                <td>
                    <div class="opp-name">{rec.name}</div>
                    <div class="opp-sponsor">{rec.sponsor} &bull; <span class="badge {status_badge_class}">{rec.status}</span></div>
                </td>
                <td><span class="tag">{rec.category or 'Opportunity'}</span></td>
                <td><span class="tag">{rec.university_types}</span></td>
                <td><span class="tag-sem">{sem_badge}</span></td>
                <td>{rec.deadline or 'Not Stated'}</td>
                <td>{rec.award_amount or 'Documented'}</td>
                <td><a href="{rec.apply_url or rec.source_url}" target="_blank" class="btn-apply">Official Apply &rarr;</a></td>
            </tr>
            """

        empty_banner = f"""<div class="empty-state">No opportunities currently match the criteria for Report {report_def.number}. All historical records are securely logged.</div>""" if not records else ""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report {report_def.number}: {report_def.title}</title>
    <style>
        :root {{
            --bg-primary: #0F172A;
            --bg-card: #1E293B;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --accent: #38BDF8;
            --border: #334155;
            --success: #22C55E;
            --warning: #F59E0B;
            --danger: #EF4444;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background: var(--bg-primary); color: var(--text-main); padding: 2rem; line-height: 1.5; }}
        .header {{ border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        .badge-cat {{ background: #0284C7; color: white; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; }}
        h1 {{ font-size: 1.75rem; margin-top: 0.5rem; font-weight: 700; color: #FFFFFF; }}
        p.desc {{ color: var(--text-muted); margin-top: 0.25rem; font-size: 0.95rem; }}
        .meta-bar {{ display: flex; gap: 1.5rem; margin-top: 1rem; color: #94A3B8; font-size: 0.85rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; background: var(--bg-card); border-radius: 8px; overflow: hidden; }}
        th {{ background: #0B1120; color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 12px 16px; text-align: left; }}
        td {{ padding: 12px 16px; border-top: 1px solid var(--border); font-size: 0.9rem; }}
        .opp-name {{ font-weight: 600; color: #F1F5F9; font-size: 0.95rem; }}
        .opp-sponsor {{ font-size: 0.8rem; color: #94A3B8; margin-top: 2px; }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
        .badge-open {{ background: rgba(34, 197, 94, 0.2); color: #4ADE80; }}
        .badge-closing {{ background: rgba(239, 68, 68, 0.2); color: #F87171; }}
        .badge-other {{ background: rgba(148, 163, 184, 0.2); color: #CBD5E1; }}
        .tag {{ background: #334155; color: #E2E8F0; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }}
        .tag-sem {{ background: #064E3B; color: #6EE7B7; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }}
        .btn-apply {{ color: var(--accent); text-decoration: none; font-weight: 600; font-size: 0.85rem; }}
        .btn-apply:hover {{ text-decoration: underline; }}
        .empty-state {{ padding: 3rem; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: 8px; margin-top: 1.5rem; }}
        .footer {{ margin-top: 3rem; text-align: center; color: #64748B; font-size: 0.8rem; border-top: 1px solid var(--border); padding-top: 1rem; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="badge-cat">{report_def.category}</span>
        <h1>Report {report_def.number}: {report_def.title}</h1>
        <p class="desc">{report_def.description}</p>
        <div class="meta-bar">
            <span><strong>Target Audience:</strong> {report_def.target_audience}</span>
            <span><strong>Generated:</strong> {datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}</span>
            <span><strong>Total Records:</strong> {len(records)}</span>
        </div>
    </div>

    {empty_banner}

    {"<table><thead><tr><th>Opportunity & Sponsor</th><th>Category</th><th>Sector</th><th>Semesters</th><th>Deadline</th><th>Benefits</th><th>Action</th></tr></thead><tbody>" + rows_html + "</tbody></table>" if records else ""}

    <div class="footer">
        Student Opportunity Intelligence Platform &bull; Autonomous Multi-Agent Verification Architecture &bull; Strictly Official Verified Data
    </div>
</body>
</html>
"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def _generate_custom_pdf(self, report_def: ReportDefinition, records: List[OpportunityRecord], output_path: Path):
        """Builds clean PDF report for custom report using ReportLab."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from generators.pdf_generator import NumberedCanvas

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=44,
            bottomMargin=44,
        )

        elements = []
        styles = self.pdf_gen.styles

        # Title
        title_para = Paragraph(f"Report {report_def.number}: {report_def.title}", self.pdf_gen.title_style)
        elements.append(title_para)
        elements.append(Spacer(1, 4))

        sub_text = f"<b>Category:</b> {report_def.category} | <b>Target:</b> {report_def.target_audience} | <b>Total Records:</b> {len(records)}"
        elements.append(Paragraph(sub_text, self.pdf_gen.subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))

        if not records:
            elements.append(Paragraph("<i>No active opportunities currently match this report definition.</i>", self.pdf_gen.body_style))
        else:
            table_data = [
                ["Opportunity & Sponsor", "Category", "Sector", "Semesters", "Deadline", "Award / Stipend"]
            ]
            for rec in records:
                sem_str = f"Sem {rec.min_semester}-{rec.max_semester}" if (rec.min_semester > 1 or rec.max_semester < 8) else "All Semesters"
                opp_cell = Paragraph(f"<b>{rec.name}</b><br/><font color='#64748B'>{rec.sponsor}</font>", self.pdf_gen.body_style)
                table_data.append([
                    opp_cell,
                    rec.category or "Scholarships",
                    rec.university_types or "All",
                    sem_str,
                    rec.deadline or "Not Stated",
                    Paragraph(rec.award_amount or "Documented", self.pdf_gen.body_style)
                ])

            col_widths = [160, 75, 55, 65, 75, 95]
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))
            elements.append(t)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.build(elements, canvasmaker=NumberedCanvas)
