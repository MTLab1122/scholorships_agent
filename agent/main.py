import os
import sys
import argparse
import logging
from pathlib import Path
from agent.pipeline import ScholarshipDailyPipeline


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
logger = logging.getLogger("scholarship_agent")


def main():
    load_env_file()
    parser = argparse.ArgumentParser(
        description="Daily Scholarship Intelligence Agent for Khyber Pakhtunkhwa (KP) & Charsadda"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="run",
        choices=["run", "sweep", "report"],
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
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Initializing Scholarship Daily Pipeline...")
    pipeline = ScholarshipDailyPipeline()

    try:
        results = pipeline.run(
            dry_run=args.dry_run,
            verify_links=not args.no_verify_links
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
