import datetime
from pathlib import Path
import pytest
from agent.models import ScholarshipRecord, ReportSummary
from generators.html_generator import HTMLReportGenerator
from generators.csv_generator import CSVReportGenerator
from generators.excel_generator import ExcelReportGenerator
from generators.pdf_generator import PDFReportGenerator


@pytest.fixture
def sample_data():
    summary = ReportSummary(
        title="Public-Sector Scholarships Intelligence Report",
        audience="Public Universities (UoP, UET Peshawar, BKUC, IMSciences)",
        generated_at_pkt="2026-10-16 07:00 PKT",
        run_id="RUN-TEST-001",
        sources_checked_count=20,
        total_opportunities=2,
        new_since_yesterday=1,
        closing_within_7_days=1,
        charsadda_eligible_count=1,
        kp_eligible_count=2,
        broken_links_count=0
    )

    rec1 = ScholarshipRecord(
        id="SCH-TEST-0001",
        name="BKUC Deserving Student Fund",
        sponsor="Bacha Khan University Charsadda",
        sponsor_type="university",
        university_types="public",
        eligible_institutions="Bacha Khan University Charsadda",
        domicile_requirements="Charsadda district domicile preferred",
        district_requirements="Charsadda",
        charsadda_flag=True,
        kp_flag=True,
        award_amount="100% Tuition Waiver",
        deadline="2026-10-20",
        days_left=4,
        status="Closing soon",
        apply_url="https://bkuc.edu.pk/apply",
        source_url="https://bkuc.edu.pk",
        verification_badge="Confirmed"
    )

    rec2 = ScholarshipRecord(
        id="SCH-TEST-0002",
        name="UoP SFAO Need-Based Fee Waiver",
        sponsor="University of Peshawar",
        sponsor_type="university",
        university_types="public",
        eligible_institutions="University of Peshawar",
        target_uni_flag=True,
        kp_flag=True,
        award_amount="50% Tuition Waiver",
        deadline="2026-11-15",
        days_left=30,
        status="Open",
        apply_url="https://uop.edu.pk/apply",
        source_url="https://uop.edu.pk",
        verification_badge="Confirmed"
    )

    return summary, [rec1, rec2]


def test_html_generator(sample_data):
    summary, records = sample_data
    gen = HTMLReportGenerator()
    html_text = gen.generate_report(
        summary=summary,
        main_records=records,
        international_records=[],
        watchlist_records=[],
        closed_records=[],
        unprocessed_sources=[],
        report_type="public"
    )

    assert "Public-Sector Scholarships Intelligence Report" in html_text
    assert "BKUC Deserving Student Fund" in html_text
    assert "Charsadda Priority" in html_text
    assert "Target Institution" in html_text or "Target Uni" in html_text
    assert "Methodology & Source Verification Framework" in html_text


def test_csv_generator(sample_data, tmp_path):
    summary, records = sample_data
    gen = CSVReportGenerator()
    csv_file = tmp_path / "test_report.csv"
    gen.generate_csv(records, csv_file)

    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8-sig")
    assert "BKUC Deserving Student Fund" in content
    assert "Charsadda" in content


def test_excel_generator(sample_data, tmp_path):
    summary, records = sample_data
    gen = ExcelReportGenerator()
    xlsx_file = tmp_path / "test_report.xlsx"
    gen.generate_excel(summary, records, [], [], xlsx_file)

    assert xlsx_file.exists()
    assert xlsx_file.stat().st_size > 1000


def test_pdf_generator(sample_data, tmp_path):
    summary, records = sample_data
    gen = PDFReportGenerator()
    pdf_file = tmp_path / "test_report.pdf"
    gen.generate_pdf(summary, records, [], [], pdf_file)

    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 1000
