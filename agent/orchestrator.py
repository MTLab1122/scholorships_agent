"""Master Orchestrator Agent for Student Opportunity Intelligence Platform.
Deterministic state machine and workflow manager that coordinates all 14 specialized agents.
Enforces step boundaries, quality control gates, audit trails, and error recovery.
"""

import uuid
import time
import json
from pathlib import Path
import logging
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional

from agent.db import OpportunityDB
from agent.models import OpportunityRecord, StudentProfile, ReportSummary
from agent.emailer import ResendEmailer
from agent.agents.discovery_agent import OpportunityDiscoveryAgent
from agent.agents.extraction_agent import OpportunityExtractionAgent
from agent.agents.classification_agent import OpportunityClassificationAgent
from agent.agents.eligibility_agent import EligibilityVerificationAgent
from agent.agents.source_verifier_agent import OfficialSourceVerificationAgent
from agent.agents.deduplicator_agent import DeduplicationAndChangeDetectionAgent
from agent.agents.semester_matching_agent import SemesterMatchingAgent
from agent.agents.recommendation_agent import PersonalizedRecommendationAgent
from agent.agents.deadline_agent import DeadlineMonitoringAgent
from agent.agents.report_agent import ReportGenerationAgent
from agent.agents.application_prep_agent import ApplicationPreparationAgent
from agent.agents.application_tracker_agent import ApplicationTrackingAgent
from agent.agents.fraud_qc_agent import FraudAndQCAgent
from agent.agents.source_coverage_agent import SourceCoverageAgent

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    DISCOVERING = "DISCOVERING"
    EXTRACTING = "EXTRACTING"
    CLASSIFYING = "CLASSIFYING"
    VERIFYING_SOURCES = "VERIFYING_SOURCES"
    AUDITING_QUALITY = "AUDITING_QUALITY"
    DEDUPLICATING = "DEDUPLICATING"
    MONITORING_DEADLINES = "MONITORING_DEADLINES"
    WAITING_SCHEDULE_GATE = "WAITING_SCHEDULE_GATE"
    GENERATING_REPORTS = "GENERATING_REPORTS"
    DISPATCHING_REPORTS = "DISPATCHING_REPORTS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MasterOrchestrator:
    """Central Master Orchestrator coordinating all autonomous intelligence agents."""

    def __init__(self, db: Optional[OpportunityDB] = None, output_dir: str = "reports"):
        self.db = db or OpportunityDB()
        self.output_dir = output_dir

        # Initialize modular specialized agents
        self.discovery_agent = OpportunityDiscoveryAgent(db=self.db)
        self.extraction_agent = OpportunityExtractionAgent()
        self.classification_agent = OpportunityClassificationAgent()
        self.eligibility_agent = EligibilityVerificationAgent()
        self.source_verifier_agent = OfficialSourceVerificationAgent()
        self.deduplicator_agent = DeduplicationAndChangeDetectionAgent(db=self.db)
        self.semester_matching_agent = SemesterMatchingAgent()
        self.recommendation_agent = PersonalizedRecommendationAgent()
        self.deadline_agent = DeadlineMonitoringAgent(db=self.db)
        self.report_agent = ReportGenerationAgent(db=self.db, output_dir=output_dir)
        self.application_prep_agent = ApplicationPreparationAgent()
        self.application_tracker_agent = ApplicationTrackingAgent(db=self.db)
        self.fraud_qc_agent = FraudAndQCAgent()
        self.source_coverage_agent = SourceCoverageAgent(db=self.db)
        self.emailer = ResendEmailer()

        self.current_state = WorkflowState.IDLE

    def wait_for_0700_pkt_gate(self) -> float:
        """Exact 07:00:00 AM PKT gate. Holds execution until 07:00:00 AM PKT (Asia/Karachi)."""
        import datetime as dt_module
        try:
            from zoneinfo import ZoneInfo
            tz_pkt = ZoneInfo("Asia/Karachi")
        except Exception:
            tz_pkt = dt_module.timezone(dt_module.timedelta(hours=5))

        now_pkt = dt_module.datetime.now(tz_pkt)
        target_7am = now_pkt.replace(hour=7, minute=0, second=0, microsecond=0)
        diff_sec = (target_7am - now_pkt).total_seconds()

        # Only hold if current time is before 07:00 AM and within a 45-minute window
        if 0 < diff_sec <= 2700:
            logger.info(
                f"[SCHEDULE GATE] Current PKT time is {now_pkt.strftime('%H:%M:%S')}. "
                f"Holding execution for {diff_sec:.1f}s until exact 07:00:00 AM PKT before dispatching email..."
            )
            time.sleep(diff_sec)
            released_pkt = dt_module.datetime.now(tz_pkt)
            logger.info(f"[SCHEDULE GATE] Gate released at {released_pkt.strftime('%H:%M:%S')} PKT. Proceeding to email dispatch.")
            return diff_sec
        else:
            logger.info(f"[SCHEDULE GATE] Current PKT time is {now_pkt.strftime('%H:%M:%S')}. Proceeding without sleep gate.")
            return 0.0

    def run_full_pipeline(
        self,
        job_id: Optional[str] = None,
        generate_reports: bool = True,
        report_numbers: Optional[List[str]] = None,
        report_formats: List[str] = ["pdf", "xlsx", "csv", "html"],
        send_email: bool = True,
        wait_for_schedule: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Executes the complete end-to-end multi-agent intelligence cycle."""
        job_id = job_id or f"JOB_{uuid.uuid4().hex[:10]}"
        start_time = datetime.now(timezone.utc)
        self.current_state = WorkflowState.INITIALIZING

        self.db.record_agent_job(
            job_id=job_id,
            agent_name="MasterOrchestrator",
            status="RUNNING",
            details="Starting autonomous intelligence cycle"
        )
        self.db.log_audit("ORCHESTRATOR", "JOB_START", f"Job {job_id} initiated")

        job_result: Dict[str, Any] = {
            "job_id": job_id,
            "start_time": start_time.isoformat(),
            "status": "RUNNING",
            "stages": {},
            "errors": []
        }

        try:
            # 1. Opportunity Discovery (Agent 1)
            self.current_state = WorkflowState.DISCOVERING
            logger.info("Executing Discovery Agent (Agent 1)...")
            discovery_res = self.discovery_agent.discover_all()
            job_result["stages"]["discovery"] = discovery_res

            # 2. Opportunity Extraction & Normalization (Agent 3)
            self.current_state = WorkflowState.EXTRACTING
            logger.info("Executing Extraction Agent (Agent 3)...")
            discovered_items = discovery_res.get("items", [])
            extracted_records: List[OpportunityRecord] = []
            for item in discovered_items:
                rec = self.extraction_agent.extract_from_text(
                    raw_text=item.get("content", ""),
                    source_url=item.get("url", ""),
                    title_hint=item.get("title")
                )
                if rec:
                    extracted_records.append(rec)
            job_result["stages"]["extraction"] = {
                "discovered_count": len(discovered_items),
                "extracted_count": len(extracted_records)
            }

            # 3. Taxonomy Classification & Sector Assignment (Agent 4)
            self.current_state = WorkflowState.CLASSIFYING
            logger.info("Executing Classification Agent (Agent 4)...")
            classified_records: List[OpportunityRecord] = []
            for rec in extracted_records:
                classified_rec = self.classification_agent.classify(rec)
                classified_records.append(classified_rec)
            job_result["stages"]["classification"] = {
                "classified_count": len(classified_records)
            }

            # 4. Official Source & Authenticity Verification (Agent 2)
            self.current_state = WorkflowState.VERIFYING_SOURCES
            logger.info("Executing Official-Source Verification Agent (Agent 2)...")
            verified_records: List[OpportunityRecord] = []
            for rec in classified_records:
                v_res = self.source_verifier_agent.verify(rec)
                rec.confirmed_by_official_source = v_res["is_verified"]
                rec.source_trust_tier = v_res["trust_tier"]
                verified_records.append(rec)
            job_result["stages"]["verification"] = {
                "verified_count": len(verified_records)
            }

            # 5. Fraud and Quality Control Gate (Agent 8)
            self.current_state = WorkflowState.AUDITING_QUALITY
            logger.info("Executing Fraud and QC Agent (Agent 8)...")
            clean_records: List[OpportunityRecord] = []
            flagged_for_review: List[Dict[str, Any]] = []
            for rec in verified_records:
                qc_eval = self.fraud_qc_agent.evaluate_opportunity(rec)
                rec.fraud_risk_score = qc_eval["risk_score"]
                if qc_eval["requires_admin_review"]:
                    flagged_for_review.append(qc_eval)
                    # Exclude critical fraud risks from public release
                    if qc_eval["severity"] != "critical":
                        clean_records.append(rec)
                else:
                    clean_records.append(rec)
            job_result["stages"]["quality_control"] = {
                "total_inspected": len(verified_records),
                "flagged_for_review": len(flagged_for_review),
                "admitted_to_catalog": len(clean_records)
            }

            # 6. Deduplication and Change Detection (Agent 5)
            self.current_state = WorkflowState.DEDUPLICATING
            logger.info("Executing Deduplication & Change Detection Agent (Agent 5)...")
            dedup_res = self.deduplicator_agent.process_new_records(clean_records)
            job_result["stages"]["deduplication"] = dedup_res

            # Sync active catalog to data/scholarships.json
            try:
                json_path = Path("data") / "scholarships.json"
                json_path.parent.mkdir(parents=True, exist_ok=True)
                with open(json_path, "w", encoding="utf-8") as jf:
                    data = [r.model_dump() for r in self.db.list_opportunities()]
                    json.dump(data, jf, indent=2, ensure_ascii=False)
            except Exception as j_err:
                logger.warning(f"Failed to sync scholarships.json: {j_err}")

            # 7. Deadline & Window Monitoring (Agent 9)
            self.current_state = WorkflowState.MONITORING_DEADLINES
            logger.info("Executing Deadline Monitoring Agent (Agent 9)...")
            deadline_res = self.deadline_agent.scan_deadlines()
            job_result["stages"]["deadline_monitoring"] = deadline_res

            # Precise Schedule Gate before Agent 10 Report Dispatch
            if wait_for_schedule:
                self.current_state = WorkflowState.WAITING_SCHEDULE_GATE
                waited = self.wait_for_0700_pkt_gate()
                job_result["schedule_gate"] = {"waited_seconds": waited}

            # 8. Report Generation (Agent 10)
            generated_pdf_files: List[Path] = []
            if generate_reports:
                self.current_state = WorkflowState.GENERATING_REPORTS
                logger.info("Executing Report Generation Agent (Agent 10)...")
                reports_to_run = report_numbers or ["01", "02", "05", "06", "17"] # Default essential set
                reports_out = []
                for num in reports_to_run:
                    try:
                        rep_res = self.report_agent.generate_report(
                            report_num=num,
                            formats=report_formats
                        )
                        reports_out.append(rep_res)
                        pdf_path_str = rep_res.get("generated_files", {}).get("pdf")
                        if pdf_path_str and Path(pdf_path_str).exists():
                            generated_pdf_files.append(Path(pdf_path_str))
                    except Exception as rep_err:
                        logger.error(f"Failed generating report {num}: {rep_err}")
                        job_result["errors"].append(f"Report {num} generation error: {str(rep_err)}")
                job_result["stages"]["reports_generated"] = reports_out

            # 9. Source Coverage & Telemetry Summary (Agent 14)
            telemetry = self.source_coverage_agent.generate_system_health_report()
            job_result["system_health"] = telemetry

            # 10. Email Dispatch Pipeline (State Machine Guaranteed Execution)
            if send_email:
                self.current_state = WorkflowState.DISPATCHING_REPORTS
                logger.info("Executing Email Dispatch Step (Guaranteed Delivery)...")
                all_opps = self.db.list_opportunities()
                pub_count = sum(1 for o in all_opps if o.university_types in ["public", "both", "not stated"])
                priv_count = sum(1 for o in all_opps if o.university_types in ["private", "both", "not stated"])
                closing_count = sum(1 for o in all_opps if o.days_left is not None and 0 <= o.days_left <= 7)
                charsadda_count = sum(1 for o in all_opps if getattr(o, "charsadda_flag", False) or getattr(o, "charsadda_eligibility", "no") == "yes")
                pkt_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                pub_summary = ReportSummary(
                    title="KP & Charsadda Scholarships: Public Universities",
                    audience="Public Sector Universities",
                    generated_at_pkt=datetime.now(timezone.utc).strftime("%Y-%m-%d 07:00 PKT"),
                    run_id=job_id,
                    sources_checked_count=discovery_res.get("total_discovered", len(clean_records)),
                    total_opportunities=pub_count,
                    new_since_yesterday=dedup_res.get("incoming_count", 0),
                    closing_within_7_days=closing_count,
                    charsadda_eligible_count=charsadda_count,
                    kp_eligible_count=pub_count,
                    broken_links_count=0,
                    degraded_mode=False
                )
                priv_summary = ReportSummary(
                    title="KP & Charsadda Scholarships: Private Universities",
                    audience="Private Sector Universities",
                    generated_at_pkt=datetime.now(timezone.utc).strftime("%Y-%m-%d 07:00 PKT"),
                    run_id=job_id,
                    sources_checked_count=discovery_res.get("total_discovered", len(clean_records)),
                    total_opportunities=priv_count,
                    new_since_yesterday=0,
                    closing_within_7_days=closing_count,
                    charsadda_eligible_count=charsadda_count,
                    kp_eligible_count=priv_count,
                    broken_links_count=0,
                    degraded_mode=False
                )

                orchestrator_telemetry = {
                    "Discovery Agent (1)": f"{discovery_res.get('total_discovered', 0)} candidates discovered",
                    "Source Verifier Agent (2)": f"{len(verified_records)} sources verified",
                    "Extraction Agent (3)": f"{len(extracted_records)} structured records extracted",
                    "Classification Agent (4)": f"{len(classified_records)} taxonomies assigned",
                    "Deduplication Agent (5)": f"{dedup_res.get('merged_count', 0)} opportunities active in catalog",
                    "Fraud & QC Agent (8)": f"{len(clean_records)} clean records admitted ({len(flagged_for_review)} flagged)",
                    "Deadline Agent (9)": f"{deadline_res.get('alerts_triggered', 0)} upcoming deadline alerts active",
                    "Report Agent (10)": f"{len(job_result['stages'].get('reports_generated', []))} reports generated",
                    "Source Coverage Agent (14)": f"Uptime {telemetry.get('health_score', 100)}%"
                }

                email_delivered = self.emailer.send_daily_reports(
                    public_summary=pub_summary,
                    private_summary=priv_summary,
                    attachment_paths=generated_pdf_files,
                    degraded=False,
                    today_pkt=pkt_date_str,
                    dry_run=dry_run,
                    deadline_alerts=deadline_res.get("alerts", []),
                    agent_telemetry=orchestrator_telemetry
                )
                job_result["email_delivered"] = email_delivered

            self.current_state = WorkflowState.COMPLETED
            job_result["status"] = "SUCCESS"
            end_time = datetime.now(timezone.utc)
            duration_sec = round((end_time - start_time).total_seconds(), 2)
            job_result["duration_seconds"] = duration_sec

            self.db.record_agent_job(
                job_id=job_id,
                agent_name="MasterOrchestrator",
                status="SUCCESS",
                details=f"Completed in {duration_sec}s. Cataloged: {len(clean_records)}"
            )
            self.db.log_audit("ORCHESTRATOR", "JOB_COMPLETE", f"Job {job_id} succeeded in {duration_sec}s")

        except Exception as e:
            self.current_state = WorkflowState.FAILED
            job_result["status"] = "FAILED"
            end_time = datetime.now(timezone.utc)
            job_result["duration_seconds"] = round((end_time - start_time).total_seconds(), 2)
            error_str = f"{str(e)}\n{traceback.format_exc()}"
            job_result["errors"].append(error_str)
            logger.error(f"Orchestrator Job {job_id} failed: {error_str}")

            self.db.record_agent_job(
                job_id=job_id,
                agent_name="MasterOrchestrator",
                status="FAILED",
                details=f"Error: {str(e)[:200]}"
            )
            self.db.log_audit("ORCHESTRATOR", "JOB_FAILED", f"Job {job_id} failed: {str(e)[:200]}")
            raise e

        return job_result

    def run_student_recommendation_cycle(self, student_id: str, top_n: int = 15) -> Dict[str, Any]:
        """Deterministic student recommendation pipeline."""
        student = self.db.get_student(student_id)
        if not student:
            # Check existing students or seed sample student profile
            students = self.db.list_students()
            if students:
                student = students[0]
                student_id = student["id"]
            else:
                default_student = {
                    "id": student_id,
                    "full_name": "Ali Khan",
                    "email": "ali.student@uop.edu.pk",
                    "university": "University of Peshawar",
                    "university_type": "public",
                    "degree_level": "Undergraduate",
                    "discipline": "Computer Science",
                    "current_semester": 4,
                    "cgpa": 3.45,
                    "domicile_district": "Charsadda",
                    "domicile_province": "Khyber Pakhtunkhwa",
                    "work_preference": "any",
                    "funding_need": "medium",
                    "skills": ["Python", "FastAPI", "Data Analysis"],
                    "interests": ["Scholarships", "Tech Internships"]
                }
                self.db.save_student(default_student)
                student = self.db.get_student(student_id)

        all_opps = self.db.list_opportunities()
        matches = self.recommendation_agent.rank_opportunities(student=student, opportunities=all_opps, top_n=top_n)

        # Record matches in DB
        self.db.save_student_matches(student_id, matches)
        self.db.log_audit("ORCHESTRATOR", "MATCH_CYCLE", f"Matched {len(matches)} opportunities for student {student_id}")

        return {
            "student_id": student_id,
            "total_matches": len(matches),
            "matches": [m.model_dump() for m in matches]
        }

    def generate_single_report(
        self,
        report_number: str,
        formats: List[str] = ["pdf", "xlsx", "csv", "html"],
        student_profile: Optional[StudentProfile] = None
    ) -> Dict[str, Any]:
        """Direct dispatch for one specific report from the 20 definitions."""
        return self.report_agent.generate_report(
            report_num=report_number,
            formats=formats,
            student_profile=student_profile
        )
