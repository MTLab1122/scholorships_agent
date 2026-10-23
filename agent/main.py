"""Main entrypoint for Student Opportunity Intelligence Platform.
Preserves existing Daily Scholarship Pipeline (actions: run, sweep, report) and adds
autonomous multi-agent orchestrator, FastAPI server, and 20-report generator.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Ensure workspace root is always in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.pipeline import ScholarshipDailyPipeline
from agent.orchestrator import MasterOrchestrator
from agent.reports_registry import REPORT_DEFINITIONS


def load_env_file(dotenv_path: Path = None):
    """Loads key=value pairs from .env into os.environ if not already set."""
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parent.parent / ".env"
    if dotenv_path.exists():
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("\"'")
                if key not in os.environ:
                    os.environ[key] = val


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("opportunity_platform")


def main():
    load_env_file()
    parser = argparse.ArgumentParser(
        description="Student Opportunity Intelligence Platform — Autonomous Multi-Agent System"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="run",
        choices=["run", "sweep", "report", "orchestrate", "server", "report-20", "match", "deadlines"],
        help="Action to execute (default: run)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline using mock extraction/discovery without calling live Gemini API"
    )
    parser.add_argument(
        "--no-verify-links",
        action="store_true",
        help="Skip HTTP GET link verification checks"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Bypass 07:00 AM PKT wait gate for immediate report and email dispatch"
    )
    parser.add_argument(
        "--report-num",
        type=str,
        default="01",
        help="Report number (01 to 20, or 'all') for 'report-20' action"
    )
    parser.add_argument(
        "--student-id",
        type=str,
        default=None,
        help="Student profile ID for 'match' action"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for 'server' action (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for 'server' action (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 1. Action: server (Launch Web Dashboard & REST API)
    if args.action == "server":
        import uvicorn
        logger.info(f"Starting Student Opportunity Intelligence Platform on http://{args.host}:{args.port}")
        uvicorn.run("agent.server:app", host=args.host, port=args.port, reload=False)
        return 0

    # 2. Action: orchestrate (Full Multi-Agent Autonomous Cycle)
    if args.action == "orchestrate":
        logger.info("Initializing Master Orchestrator Agent...")
        orchestrator = MasterOrchestrator()
        result = orchestrator.run_full_pipeline(
            generate_reports=True,
            send_email=True,
            wait_for_schedule=not args.no_wait,
            dry_run=args.dry_run
        )
        logger.info(f"=== Multi-Agent Orchestrator Result: {result['status']} in {result.get('duration_seconds', 0)}s ===")
        for stage, data in result.get("stages", {}).items():
            logger.info(f"  Stage [{stage}]: {data}")
        return 0 if result["status"] == "SUCCESS" else 1

    # 3. Action: report-20 (Modular 20 Reports Generation)
    if args.action == "report-20":
        orchestrator = MasterOrchestrator()
        target_reports = [r.number for r in REPORT_DEFINITIONS] if args.report_num.lower() == "all" else [args.report_num.zfill(2)]
        logger.info(f"Generating Report(s): {target_reports}")
        for num in target_reports:
            res = orchestrator.generate_single_report(num, formats=["pdf", "xlsx", "csv", "html"])
            logger.info(f"Report {num} [{res['title']}]: {res['record_count']} records generated.")
            for fmt, path in res["generated_files"].items():
                logger.info(f"  - {fmt.upper()}: {path}")
        return 0

    # 4. Action: match (Personalized Student Recommendation Matching)
    if args.action == "match":
        orchestrator = MasterOrchestrator()
        from agent.db import OpportunityDB
        db = OpportunityDB()
        students = db.list_students()
        target_sid = args.student_id or (students[0]["id"] if students else None)
        if not target_sid:
            logger.error("No student profiles exist in the database. Please create one first.")
            return 1
        res = orchestrator.run_student_recommendation_cycle(target_sid)
        logger.info(f"=== Matches for Student {target_sid}: {res['total_matches']} Found ===")
        for idx, m in enumerate(res["matches"][:10], 1):
            logger.info(f"{idx}. [{m['match_score']}% Match] {m['opportunity_name']} ({m['sponsor']})")
            for reason in m["reasons"][:2]:
                logger.info(f"    - {reason}")
        return 0

    # 5. Action: deadlines (Scan and monitor deadline alerts)
    if args.action == "deadlines":
        orchestrator = MasterOrchestrator()
        alerts_summary = orchestrator.deadline_agent.scan_deadlines()
        logger.info(f"=== Deadlines Scanned: {alerts_summary['total_checked']} opportunities ===")
        logger.info(f"Alerts Triggered: {alerts_summary['alerts_triggered']}, Notifications Saved: {alerts_summary['notifications_saved']}")
        for a in alerts_summary["alerts"][:10]:
            logger.info(f"  [{a['urgency']}] {a['opportunity_name']} - Deadline: {a['deadline']} ({a['days_left']} days left)")
        return 0

    # 6. Default Actions: run, sweep, report (Preserved Daily Scholarship Pipeline)
    logger.info("Initializing Scholarship Daily Pipeline...")
    pipeline = ScholarshipDailyPipeline()

    try:
        results = pipeline.run(
            dry_run=args.dry_run,
            verify_links=not args.no_verify_links,
            wait_for_schedule=not args.no_wait
        )
        logger.info("=== Pipeline Execution Complete ===")
        logger.info(f"Run ID: {results['run_id']}")
        logger.info(f"Public Opportunities: {results['public_opportunities']}")
        logger.info(f"Private Opportunities: {results['private_opportunities']}")
        logger.info(f"Degraded Mode: {results['degraded']}")
        logger.info(f"Email Sent: {results['email_sent']}")
        logger.info("Generated Report Files:")
        for f in results["generated_files"]:
            logger.info(f"  - {f}")
        return 0
    except Exception as e:
        logger.exception(f"Fatal error during pipeline execution: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
