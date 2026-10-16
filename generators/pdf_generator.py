"""PDF Report Generator using ReportLab.
Produces structured, publication-ready PDF reports with headers, tables,
and opportunity summaries for printing and downloading.
"""

from pathlib import Path
from typing import List, Union
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from agent.models import ScholarshipRecord, ReportSummary


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 810, "KP & Charsadda Daily Scholarship Intelligence Agent — Official Verified Report")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 804, 559, 804)

        # Footer (all pages)
        footer_text = f"Page {self._pageNumber} of {page_count} | Khyber Pakhtunkhwa & Charsadda Domicile"
        self.drawRightString(559, 24, footer_text)
        self.drawString(36, 24, "Strictly Verified against Official Domains (*.gov.pk, *.edu.pk)")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 34, 559, 34)
        self.restoreState()


class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.title_style = ParagraphStyle(
            "DocTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F172A")
        )
        self.subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#475569")
        )
        self.section_h1 = ParagraphStyle(
            "SectionH1",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=6
        )
        self.body_style = ParagraphStyle(
            "BodySmall",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1E293B")
        )
        self.body_bold = ParagraphStyle(
            "BodyBold",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0F172A")
        )
        self.badge_charsadda = ParagraphStyle(
            "BadgeCharsadda",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#B45309")
        )

    def generate_pdf(
        self,
        summary: ReportSummary,
        main_records: List[ScholarshipRecord],
        international_records: List[ScholarshipRecord],
        watchlist_records: List[ScholarshipRecord],
        output_path: Union[str, Path]
    ) -> None:
        """Builds PDF document."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=45,
            bottomMargin=45
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph(summary.title, self.title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Audience: {summary.audience}", self.subtitle_style))
        story.append(Paragraph(
            f"Last Checked: <b>{summary.generated_at_pkt}</b> | Run ID: <b>{summary.run_id}</b> | "
            f"Sources Audited: <b>{summary.sources_checked_count}</b> | Opportunities: <b>{summary.total_opportunities}</b>",
            self.subtitle_style
        ))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284C7"), spaceAfter=12))

        # 2. Executive Metrics Summary Table
        metrics_data = [
            [
                Paragraph("<b>Total Active</b>", self.body_style),
                Paragraph("<b>New Today</b>", self.body_style),
                Paragraph("<b>Closing ≤ 7d</b>", self.body_style),
                Paragraph("<b>Charsadda Eligible</b>", self.body_style),
                Paragraph("<b>KP Eligible</b>", self.body_style),
                Paragraph("<b>Broken Links</b>", self.body_style),
            ],
            [
                Paragraph(f"<font size=12><b>{summary.total_opportunities}</b></font>", self.body_style),
                Paragraph(f"<font size=12><b>{summary.new_since_yesterday}</b></font>", self.body_style),
                Paragraph(f"<font size=12 color='#B91C1C'><b>{summary.closing_within_7_days}</b></font>", self.body_style),
                Paragraph(f"<font size=12 color='#B45309'><b>{summary.charsadda_eligible_count}</b></font>", self.body_style),
                Paragraph(f"<font size=12 color='#15803D'><b>{summary.kp_eligible_count}</b></font>", self.body_style),
                Paragraph(f"<font size=12><b>{summary.broken_links_count}</b></font>", self.body_style),
            ]
        ]
        metrics_table = Table(metrics_data, colWidths=[87] * 6)
        metrics_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BORDER", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 14))

        # 3. Main Opportunities Table
        story.append(Paragraph("Verified Active Opportunities (Sorted by Soonest Deadline)", self.section_h1))
        
        table_data = [
            [
                Paragraph("<b>Opportunity & Sponsor</b>", self.body_bold),
                Paragraph("<b>Status</b>", self.body_bold),
                Paragraph("<b>Deadline</b>", self.body_bold),
                Paragraph("<b>Priority Badges</b>", self.body_bold),
                Paragraph("<b>Award Summary</b>", self.body_bold),
                Paragraph("<b>Verification</b>", self.body_bold),
            ]
        ]

        for r in main_records[:20]: # Keep concise in PDF overview
            badges_txt = []
            if r.charsadda_flag:
                badges_txt.append("<font color='#B45309'><b>CHARSADDA</b></font>")
            if r.target_uni_flag:
                badges_txt.append("<font color='#7E22CE'><b>TARGET UNI</b></font>")
            if r.kp_flag and not badges_txt:
                badges_txt.append("<font color='#15803D'>KP Domicile</font>")

            table_data.append([
                Paragraph(f"<b>{r.name}</b><br/><font color='#64748B'>{r.sponsor}</font>", self.body_style),
                Paragraph(r.status, self.body_style),
                Paragraph(f"<b>{r.deadline}</b>" + (f"<br/><font color='#B91C1C'>({r.days_left}d left)</font>" if r.days_left is not None and r.days_left <= 7 else ""), self.body_style),
                Paragraph(" | ".join(badges_txt) if badges_txt else "General", self.body_style),
                Paragraph(r.award_amount, self.body_style),
                Paragraph(f"<b>{r.verification_badge}</b>", self.body_style),
            ])

        if len(table_data) == 1:
            table_data.append([Paragraph("No active opportunities found.", self.body_style)] * 6)

        main_table = Table(table_data, colWidths=[140, 70, 70, 80, 110, 53])
        main_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(main_table)
        story.append(Spacer(1, 14))

        # 4. Opportunity Detail Cards (Top Highlighted Items)
        story.append(Paragraph("Opportunity Detail Specifications", self.section_h1))
        for r in main_records[:8]:
            card_data = [
                [
                    Paragraph(f"<b>{r.name}</b> — <i>{r.sponsor}</i> ({r.sponsor_type})", self.body_bold),
                    Paragraph(f"Deadline: <b>{r.deadline}</b> | Status: <b>{r.status}</b>", self.body_style)
                ],
                [
                    Paragraph(
                        f"<b>Eligible Unis:</b> {r.eligible_institutions} ({r.university_types})<br/>"
                        f"<b>Degrees:</b> {r.degree_levels} | <b>Fields:</b> {r.fields_of_study}<br/>"
                        f"<b>Domicile/District:</b> {r.domicile_requirements} (Charsadda: {r.charsadda_eligibility})<br/>"
                        f"<b>Merit/Need Criteria:</b> Min: {r.min_gpa_or_marks} | Cap: {r.income_cap}<br/>"
                        f"<b>Award:</b> {r.award_amount} | <b>Duration:</b> {r.duration}<br/>"
                        f"<b>Application Procedure:</b> {r.application_procedure}<br/>"
                        f"<b>Required Docs:</b> {r.required_documents}<br/>"
                        f"<b>Apply URL:</b> <font color='#0284C7'>{r.apply_url}</font><br/>"
                        f"<b>Official Quote:</b> <i>&ldquo;{r.evidence_quote}&rdquo;</i>",
                        self.body_style
                    ),
                    Paragraph(f"Verification: <b>{r.verification_badge}</b><br/>Source: {r.source_url[:40]}...", self.body_style)
                ]
            ]
            card_table = Table(card_data, colWidths=[390, 133])
            card_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(card_table)
            story.append(Spacer(1, 8))

        # 5. International Section
        if international_records:
            story.append(Spacer(1, 8))
            story.append(Paragraph("International Scholarships (Open to Pakistani & KP Students)", self.section_h1))
            intl_data = [
                [
                    Paragraph("<b>Scheme</b>", self.body_bold),
                    Paragraph("<b>Sponsor</b>", self.body_bold),
                    Paragraph("<b>Deadline</b>", self.body_bold),
                    Paragraph("<b>Benefits</b>", self.body_bold),
                    Paragraph("<b>Portal Link</b>", self.body_bold)
                ]
            ]
            for r in international_records:
                intl_data.append([
                    Paragraph(r.name, self.body_style),
                    Paragraph(r.sponsor, self.body_style),
                    Paragraph(r.deadline, self.body_style),
                    Paragraph(r.award_amount, self.body_style),
                    Paragraph(r.apply_url, self.body_style),
                ])
            intl_table = Table(intl_data, colWidths=[130, 110, 70, 113, 100])
            intl_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(intl_table)

        # 6. Disclaimer
        story.append(Spacer(1, 14))
        disclaimer_text = (
            "<b>Official Verification & Anti-Fraud Notice:</b> All opportunities are crawled strictly from official "
            "government (*.gov.pk), university (*.edu.pk) and registered non-profit portals. No paid consultancies or "
            "unverified third-party schemes are included. Students must verify document attestation requirements with their "
            "university Students Financial Aid Office (SFAO) before submission."
        )
        story.append(Paragraph(disclaimer_text, self.body_style))

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
