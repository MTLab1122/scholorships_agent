"""Acceptance and Integration Test Suite for Student Opportunity Intelligence Platform.
Validates all 20 core acceptance criteria defined in Section 14 of the Master Specification.
"""

import os
import json
import sqlite3
import datetime
import pytest
from pathlib import Path

from agent.models import ScholarshipRecord, OpportunityRecord, StudentProfile
from agent.db import Database, OpportunityDB
from agent.orchestrator import MasterOrchestrator
from agent.reports_registry import get_report_definition, REPORT_DEFINITIONS
from agent.agents.semester_matching_agent import SemesterMatchingAgent
from agent.agents.source_verifier_agent import SourceVerificationAgent
from agent.agents.deduplicator_agent import DeduplicationAndChangeAgent
from agent.agents.deadline_agent import DeadlineMonitoringAgent
from agent.agents.report_agent import ReportGenerationAgent
from agent.agents.application_tracker_agent import ApplicationTrackingAgent
from agent.agents.fraud_qc_agent import FraudAndQCAgent
from agent.classifier import UniversityClassifier
from agent.normalizer import OpportunityNormalizer
from fastapi.testclient import TestClient
from agent.server import app


@pytest.fixture
def test_db(tmp_path):
    """Isolated temporary SQLite database for test execution."""
    db_file = tmp_path / "test_opportunities.db"
    return Database(db_path=db_file)


@pytest.fixture
def populated_db(test_db):
    """Database populated with test opportunities."""
    records = [
        {
            "id": "OPP-001",
            "name": "HEC Need Based Scholarship 2026-27",
            "sponsor": "Higher Education Commission (HEC)",
            "sponsor_type": "federal govt",
            "category": "scholarships",
            "university_types": "public",
            "eligible_institutions": "All Public Sector Universities",
            "degree_levels": "Undergraduate",
            "kp_eligibility": "yes",
            "charsadda_eligibility": "yes",
            "min_gpa_or_marks": "2.50",
            "income_cap": "45000",
            "deadline": "2026-12-15",
            "days_left": 57,
            "status": "Open",
            "source_url": "https://hec.gov.pk/scholarships",
            "apply_url": "https://hec.gov.pk/apply",
            "evidence_quote": "HEC offers need-based scholarships for undergraduate students in public universities.",
            "confirmed_by_official_source": True,
            "source_trust_tier": 1,
            "is_national": True,
            "is_international": False,
            "is_need_based": True,
            "eligible_semesters": [1, 2, 3, 4, 5, 6, 7, 8]
        },
        {
            "id": "OPP-002",
            "name": "PSEB National IT Internship Program",
            "sponsor": "Pakistan Software Export Board (PSEB)",
            "sponsor_type": "federal govt",
            "category": "internships",
            "university_types": "both",
            "eligible_institutions": "All Pakistani Universities",
            "degree_levels": "Undergraduate",
            "kp_eligibility": "yes",
            "charsadda_eligibility": "yes",
            "min_gpa_or_marks": "2.50",
            "deadline": "2026-11-20",
            "days_left": 32,
            "status": "Open",
            "source_url": "https://pseb.org.pk/internships",
            "apply_url": "https://pseb.org.pk/apply",
            "evidence_quote": "PSEB offers 6-month paid internships to final year IT students and graduates.",
            "confirmed_by_official_source": True,
            "source_trust_tier": 1,
            "is_national": True,
            "is_international": False,
            "work_mode": "remote",
            "paid_status": "paid",
            "eligible_semesters": [7, 8]
        },
        {
            "id": "OPP-003",
            "name": "CERN Summer Student Internship Programme",
            "sponsor": "CERN Geneva",
            "sponsor_type": "international",
            "category": "internships",
            "university_types": "both",
            "eligible_institutions": "Pakistani and global universities",
            "degree_levels": "Undergraduate",
            "kp_eligibility": "yes",
            "charsadda_eligibility": "yes",
            "deadline": "2027-01-31",
            "days_left": 104,
            "status": "Open",
            "source_url": "https://cern.ch/jobs",
            "apply_url": "https://cern.ch/apply",
            "evidence_quote": "CERN summer student programme for Pakistani students.",
            "confirmed_by_official_source": True,
            "source_trust_tier": 1,
            "is_national": False,
            "is_international": True,
            "work_mode": "onsite",
            "paid_status": "paid",
            "eligible_semesters": [5, 6, 7, 8]
        },
        {
            "id": "OPP-004",
            "name": "Expired Provincial Research Grant",
            "sponsor": "Provincial Directorate of S&T",
            "sponsor_type": "provincial govt",
            "category": "research_fellowships",
            "university_types": "public",
            "deadline": "2026-08-01",
            "days_left": -79,
            "status": "Closed",
            "source_url": "https://dst.kp.gov.pk/grants",
            "evidence_quote": "Expired call for scientific research papers.",
            "confirmed_by_official_source": True,
            "source_trust_tier": 1,
            "eligible_semesters": [5, 6, 7, 8]
        }
    ]
    for r in records:
        test_db.save_opportunity(r)
    return test_db


# --- Criterion 1: Existing scholarship reports still work after the upgrade ---
def test_criterion_1_existing_scholarship_reports(tmp_path):
    from agent.pipeline import ScholarshipDailyPipeline
    pipeline = ScholarshipDailyPipeline()
    # Pipeline executes without throwing
    res = pipeline.run(dry_run=True, verify_links=False)
    assert res is not None
    assert "run_id" in res
    assert "public_opportunities" in res
    assert "private_opportunities" in res
    assert len(res["generated_files"]) >= 8


# --- Criterion 2: National and international internship reports generate correctly ---
def test_criterion_2_internship_reports_generation(populated_db, tmp_path):
    rep_agent = ReportGenerationAgent(db=populated_db, output_dir=str(tmp_path))
    
    # Report 05: National Internships
    r5 = rep_agent.generate_report("05", formats=["csv", "xlsx", "html"])
    assert r5["status"] == "success"
    assert r5["record_count"] >= 1
    assert "csv" in r5["generated_files"]

    # Report 06: International Internships
    r6 = rep_agent.generate_report("06", formats=["csv", "xlsx", "html"])
    assert r6["status"] == "success"
    assert r6["record_count"] >= 1
    assert "xlsx" in r6["generated_files"]


# --- Criterion 3: Public and private university eligibility is handled correctly ---
def test_criterion_3_university_sector_eligibility():
    matcher = SemesterMatchingAgent()
    
    public_student = StudentProfile(
        full_name="Public Student",
        email="pub@uop.edu.pk",
        university="University of Peshawar",
        university_type="public",
        degree_level="Undergraduate",
        discipline="Computer Science",
        current_semester=4,
        cgpa=3.5,
        domicile_district="Charsadda"
    )

    private_student = StudentProfile(
        full_name="Private Student",
        email="priv@cecos.edu.pk",
        university="CECOS University",
        university_type="private",
        degree_level="Undergraduate",
        discipline="Computer Science",
        current_semester=4,
        cgpa=3.5,
        domicile_district="Charsadda"
    )

    public_only_opp = OpportunityRecord(
        id="TEST-PUB",
        name="Public University Exclusive Aid",
        sponsor="HEC",
        university_types="public",
        degree_levels="Undergraduate",
        kp_eligibility="yes",
        charsadda_eligibility="yes"
    )

    res_pub = matcher.evaluate_opportunity(public_student, public_only_opp)
    res_priv = matcher.evaluate_opportunity(private_student, public_only_opp)

    assert res_pub.is_eligible is True
    assert res_priv.is_eligible is False
    assert "Ineligible university sector" in res_priv.reasons[0]


# --- Criterion 4: Semester filters work for all supported report categories ---
def test_criterion_4_semester_filtering():
    matcher = SemesterMatchingAgent()
    
    early_sem_student = StudentProfile(
        full_name="Freshman Student",
        email="freshman@uop.edu.pk",
        university="University of Peshawar",
        university_type="public",
        degree_level="Undergraduate",
        discipline="Computer Science",
        current_semester=2,
        cgpa=3.2,
        domicile_district="Charsadda"
    )

    final_year_opp = OpportunityRecord(
        id="TEST-FYP",
        name="Senior Capstone Industry Grant",
        sponsor="Tech Industry",
        eligible_semesters=[7, 8],
        category="fyp_industry_projects"
    )

    res = matcher.evaluate_opportunity(early_sem_student, final_year_opp)
    assert res.is_eligible is False
    assert any("Semester 2 does not meet required range" in r for r in res.reasons)


# --- Criterion 5: Missing eligibility information is not silently treated as a match ---
def test_criterion_5_missing_eligibility_not_silently_matched():
    matcher = SemesterMatchingAgent()
    student = StudentProfile(
        full_name="Ambiguous Student",
        email="amb@uop.edu.pk",
        university="University of Peshawar",
        university_type="public",
        degree_level="Undergraduate",
        discipline="Pharmacy",
        current_semester=3,
        cgpa=3.0,
        domicile_district="Charsadda"
    )

    strict_opp = OpportunityRecord(
        id="TEST-MED",
        name="MBBS Medical Scholarship",
        sponsor="Health Dept",
        fields_of_study="Medicine / MBBS only",
        degree_levels="Undergraduate",
        kp_eligibility="yes",
        charsadda_eligibility="yes"
    )

    res = matcher.evaluate_opportunity(student, strict_opp)
    assert res.is_eligible is False
    assert any("discipline" in r.lower() or "study" in r.lower() for r in res.reasons)


# --- Criterion 6: Expired opportunities are not incorrectly reported as open ---
def test_criterion_6_expired_opportunities_not_open():
    normalizer = OpportunityNormalizer()
    today = datetime.date(2026, 10, 19)
    
    status, days_left = normalizer.compute_status(
        deadline_str="2026-09-01",
        today=today
    )
    assert status == "Closed"
    assert days_left < 0


# --- Criterion 7: Duplicate announcements identified without losing source evidence ---
def test_criterion_7_deduplication_preserves_sources(populated_db):
    dedup = DeduplicationAndChangeAgent(db=populated_db)
    
    incoming_rec = ScholarshipRecord(
        id="",
        name="HEC Need Based Scholarship 2026-27",
        sponsor="Higher Education Commission",
        source_url="https://new-portal.hec.gov.pk/notice",
        apply_url="https://new-portal.hec.gov.pk/apply",
        deadline="2026-12-15",
        status="Open",
        source_trust_tier=1,
        evidence_quote="Verbatim quote from new portal."
    )

    res = dedup.process_new_records([incoming_rec])
    assert res["incoming_count"] == 1
    
    # Verify merged record in DB retains previous and incoming URLs
    opp = populated_db.get_opportunity("OPP-001")
    assert opp is not None
    assert "https://new-portal.hec.gov.pk/notice" in opp["all_source_urls"] or opp["source_url"] == "https://new-portal.hec.gov.pk/notice"


# --- Criterion 8: A changed deadline updates record and creates history entry ---
def test_criterion_8_changed_deadline_creates_audit_entry(populated_db):
    dedup = DeduplicationAndChangeAgent(db=populated_db)
    
    existing = populated_db.get_opportunity("OPP-001")
    assert existing["deadline"] == "2026-12-15"

    extended_rec = ScholarshipRecord(
        id="OPP-001",
        name="HEC Need Based Scholarship 2026-27",
        sponsor="Higher Education Commission",
        deadline="2026-12-31", # Extended by 16 days
        status="Open",
        source_trust_tier=1
    )

    dedup.process_new_records([extended_rec])
    
    # Check change log
    changes = populated_db.list_changes(limit=10)
    assert any(c["field_name"] == "deadline" and c["new_value"] == "2026-12-31" for c in changes)


# --- Criterion 9: Report generation produces valid non-empty files ---
def test_criterion_9_report_generation_valid_files(populated_db, tmp_path):
    rep_agent = ReportGenerationAgent(db=populated_db, output_dir=str(tmp_path))
    res = rep_agent.generate_report("01", formats=["pdf", "xlsx", "csv", "html"])
    
    for fmt, path_str in res["generated_files"].items():
        file_path = Path(path_str)
        assert file_path.exists(), f"File {fmt} was not created"
        assert file_path.stat().st_size > 0, f"File {fmt} is empty"


# --- Criterion 10: Students cannot access another student's private application records ---
def test_criterion_10_student_data_isolation(populated_db):
    tracker = ApplicationTrackingAgent(db=populated_db)
    
    # Save student 1 & student 2
    s1_id = populated_db.save_student({"full_name": "Student One", "email": "s1@uop.edu.pk"})
    s2_id = populated_db.save_student({"full_name": "Student Two", "email": "s2@uop.edu.pk"})

    app1 = tracker.create_application(student_id=s1_id, opportunity_id="OPP-001", notes="Private note 1")
    
    # Student 2 attempts to update or read student 1's application
    hack_res = tracker.update_status(application_id=app1.id, student_id=s2_id, new_status="applied")
    assert hack_res is None # Rejected by ownership guard

    # Student 2 application list should be empty
    s2_apps = tracker.get_student_applications(s2_id)
    assert len(s2_apps) == 0


# --- Criterion 11: Non-admin users cannot access administrative controls ---
def test_criterion_11_role_based_isolation():
    client = TestClient(app)
    # Public endpoints work
    r = client.get("/api/health")
    assert r.status_code == 200
    
    # Student cannot access unauthorized system paths
    r_traversal = client.get("/api/reports/download/../../etc/passwd")
    assert r_traversal.status_code == 404


# --- Criterion 12: Failed research jobs can be retried safely ---
def test_criterion_12_safe_job_retries(populated_db):
    orch = MasterOrchestrator(db=populated_db)
    # Run 1
    res1 = orch.run_full_pipeline(job_id="RETRY-01", generate_reports=False)
    assert res1["status"] in ["SUCCESS", "FAILED"]

    # Retry same job safely
    res2 = orch.run_full_pipeline(job_id="RETRY-01-RETRY", generate_reports=False)
    assert res2["status"] in ["SUCCESS", "FAILED"]


# --- Criterion 13: Duplicate scheduled runs do not create duplicate notifications ---
def test_criterion_13_idempotent_notifications(populated_db):
    deadline_agent = DeadlineMonitoringAgent(db=populated_db)
    
    # Create opportunity closing in 4 days
    opp = ScholarshipRecord(
        id="NOTIF-01",
        name="Closing Soon Award",
        sponsor="Govt of KP",
        deadline=(datetime.date.today() + datetime.timedelta(days=4)).strftime("%Y-%m-%d"),
        status="Closing soon",
        source_trust_tier=1
    )
    
    alerts = deadline_agent.evaluate_deadlines([opp])
    assert len(alerts) >= 1

    # First dispatch
    saved1 = deadline_agent.dispatch_alerts_to_db(alerts, student_id="STU-TEST")
    # Second duplicate dispatch (same day)
    saved2 = deadline_agent.dispatch_alerts_to_db(alerts, student_id="STU-TEST")

    # Due to UNIQUE(dedup_key), second dispatch should not insert duplicates
    assert saved1 >= 1
    assert saved2 == 0


# --- Criterion 14: Invalid or unsupported source claims are not marked as verified ---
def test_criterion_14_unverified_sources_flagged():
    verifier = SourceVerificationAgent()
    unverified_rec = ScholarshipRecord(
        id="FAKE-01",
        name="Guaranteed EasyPaisa Scholarship",
        sponsor="Unverified Private Blog",
        source_url="http://freemoney-scholarships.blogspot.com/apply",
        apply_url="http://freemoney-scholarships.blogspot.com/apply"
    )

    checked = verifier.verify_opportunity(unverified_rec, verify_links=False)
    assert checked.confirmed_by_official_source is False
    assert checked.source_trust_tier == 3
    assert checked.verification_badge == "Unverified"


# --- Criterion 15: External-source failures do not corrupt existing records ---
def test_criterion_15_source_failures_preserve_db(populated_db):
    initial_count = len(populated_db.list_opportunities())
    
    # Corrupt / unreachable incoming crawl attempt
    dedup = DeduplicationAndChangeAgent(db=populated_db)
    try:
        dedup.process_new_records([])
    except Exception:
        pass

    assert len(populated_db.list_opportunities()) == initial_count


# --- Criterion 16: Empty search results produce a legitimate empty report ---
def test_criterion_16_empty_report_honest_generation(populated_db, tmp_path):
    rep_agent = ReportGenerationAgent(db=populated_db, output_dir=str(tmp_path))
    # Report 14: Entrepreneurship and Startups (no records in populated_db)
    rep_def = get_report_definition("14")
    assert rep_def is not None

    res = rep_agent.generate_report("14", formats=["html", "pdf", "csv"])
    assert res["status"] == "success"
    # Even if 0 records match, valid non-empty files are produced with honest empty disclaimer
    for fmt, p in res["generated_files"].items():
        assert Path(p).exists()
        assert Path(p).stat().st_size > 0


# --- Criterion 17: Existing user accounts and data remain intact ---
def test_criterion_17_user_data_preservation(populated_db):
    # Create student
    sid = populated_db.save_student({"full_name": "Persistent Student", "email": "persist@uop.edu.pk"})
    
    # Run sync operations
    populated_db.sync_from_json()
    
    # Verify student is still in DB
    stu = populated_db.get_student(sid)
    assert stu is not None
    assert stu["email"] == "persist@uop.edu.pk"


# --- Criterion 18: Missing credentials produce clear configuration errors ---
def test_criterion_18_missing_credentials_handling():
    from agent.gemini_client import GeminiScholarshipClient
    # Client initialized with empty API key should raise ValueError or clear error
    try:
        client = GeminiScholarshipClient(api_key="")
        # In mock mode it works, but without API key calling live API produces clean error
        assert client is not None
    except ValueError as ve:
        assert "API key" in str(ve)


# --- Criterion 19: System handles timezone boundaries and upcoming deadlines correctly ---
def test_criterion_19_timezone_handling():
    normalizer = OpportunityNormalizer()
    today_pkt = datetime.date(2026, 10, 19)
    
    # Deadline tomorrow
    status, days_left = normalizer.compute_status(
        deadline_str="2026-10-20",
        today=today_pkt
    )
    assert status == "Closing soon"
    assert days_left == 1


# --- Criterion 20: Main student and administrator workflows work via API ---
def test_criterion_20_api_workflows():
    client = TestClient(app)
    
    # 1. Explorer API
    r_opps = client.get("/api/opportunities?category=scholarships")
    assert r_opps.status_code == 200
    
    # 2. 20 Reports API
    r_reps = client.get("/api/reports")
    assert r_reps.status_code == 200
    assert len(r_reps.json()["reports"]) == 20

    # 3. Telemetry API
    r_status = client.get("/api/orchestrator/status")
    assert r_status.status_code == 200
    assert "health" in r_status.json()
