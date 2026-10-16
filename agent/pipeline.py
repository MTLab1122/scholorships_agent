"""Daily Scholarship Pipeline Orchestrator.
Executes the complete daily workflow:
1. Load state from data/scholarships.json
2. Seed sweep from config/sources.yaml
3. Discovery queries via Gemini search grounding
4. Structured extraction via Gemini
5. Normalization, date parsing, status, trust tiers, link verification
6. Priority flags & HEC sector classification (IMSciences = public)
7. Deduplication, merging, and state retention
8. Split into Public and Private university reports
9. Render HTML, PDF, XLSX, and CSV into reports/YYYY-MM-DD/
10. Email reports via Resend with attachments
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse

from agent.models import (
    ScholarshipRecord,
    ScholarshipExtractionItem,
    ReportSummary
)
from agent.yaml_utils import load_yaml
from agent.classifier import UniversityClassifier
from agent.fetcher import ContentFetcher, PageContent
from agent.gemini_client import GeminiScholarshipClient
from agent.normalizer import OpportunityNormalizer
from agent.deduplicator import ScholarshipDeduplicator
from agent.emailer import ResendEmailer
from generators.html_generator import HTMLReportGenerator
from generators.csv_generator import CSVReportGenerator
from generators.excel_generator import ExcelReportGenerator
from generators.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)

PKT_TIMEZONE = datetime.timezone(datetime.timedelta(hours=5))


class ScholarshipDailyPipeline:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(__file__).resolve().parent.parent
        self._load_env_file(self.workspace_root / ".env")
        self.config_dir = self.workspace_root / "config"
        self.data_dir = self.workspace_root / "data"
        self.reports_dir = self.workspace_root / "reports"

        self.settings = self._load_settings()
        self.sources_cfg = self._load_sources()

        self.classifier = UniversityClassifier(self.config_dir / "universities.json")
        self.fetcher = ContentFetcher(
            user_agent=self.settings.get("pipeline", {}).get("browser_user_agent", "ScholarshipVerificationAgent/1.0"),
            timeout=self.settings.get("pipeline", {}).get("request_timeout_seconds", 25),
            follow_links_per_seed=self.settings.get("pipeline", {}).get("follow_links_per_seed", 5)
        )
        model_name = os.environ.get("GEMINI_MODEL") or self.settings.get("gemini", {}).get("model", "gemini-3.8-flash")
        self.gemini_client = GeminiScholarshipClient(
            primary_model=model_name,
            fallback_model=self.settings.get("gemini", {}).get("fallback_model", "gemini-3.5-flash-lite"),
            max_retries=self.settings.get("gemini", {}).get("max_retries", 3),
            backoff_factor=self.settings.get("gemini", {}).get("retry_backoff_factor", 2.0)
        )
        self.normalizer = OpportunityNormalizer(
            current_cycle=self.settings.get("cycle", "2026-27"),
            user_agent=self.settings.get("pipeline", {}).get("browser_user_agent", "ScholarshipVerificationAgent/1.0"),
            timeout=self.settings.get("pipeline", {}).get("request_timeout_seconds", 15)
        )
        self.deduplicator = ScholarshipDeduplicator(
            fuzzy_threshold=0.88,
            drop_after_days_unseen=self.settings.get("pipeline", {}).get("drop_after_days_unseen", 30)
        )
        self.emailer = ResendEmailer()

        # Generators
        self.html_gen = HTMLReportGenerator()
        self.csv_gen = CSVReportGenerator()
        self.excel_gen = ExcelReportGenerator()
        self.pdf_gen = PDFReportGenerator()

    def _load_env_file(self, path: Path) -> None:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    if key not in os.environ:
                        os.environ[key] = val

    def _load_settings(self) -> Dict[str, Any]:
        settings_path = self.config_dir / "settings.yaml"
        if settings_path.exists():
            return load_yaml(settings_path)
        return {}

    def _load_sources(self) -> Dict[str, Any]:
        sources_path = self.config_dir / "sources.yaml"
        if sources_path.exists():
            return load_yaml(sources_path)
        return {"sources": []}

    def run(self, dry_run: bool = False, verify_links: bool = True) -> Dict[str, Any]:
        """Runs the complete daily scholarship pipeline."""
        now_pkt = datetime.datetime.now(PKT_TIMEZONE)
        today_date = now_pkt.date()
        today_str = today_date.strftime("%Y-%m-%d")
        time_pkt_str = now_pkt.strftime("%Y-%m-%d %H:%M PKT")
        run_id = f"RUN-{now_pkt.strftime('%Y%m%d-%H%M%S')}"

        logger.info(f"Starting Scholarship Daily Pipeline. Run ID: {run_id} at {time_pkt_str}")

        # Step 1: Load stored historical state
        state_file = self.data_dir / "scholarships.json"
        previous_records = self._load_state(state_file)
        logger.info(f"Loaded {len(previous_records)} historical records from {state_file}")

        # Step 2: Seed sweep
        seed_sources = self.sources_cfg.get("sources", [])
        total_seeds = len(seed_sources)
        failed_sources = []
        fetched_pages: List[PageContent] = []
        discovered_urls_set = set()

        if dry_run:
            logger.info("Executing seed sweep in dry-run mode (using mock seed pages).")
            fetched_pages = [
                PageContent("https://bkuc.edu.pk/financial-aid", "Bacha Khan University Charsadda Financial Aid", {}, tier=1, category="university"),
                PageContent("https://www.uop.edu.pk/sfao/", "University of Peshawar SFAO Notice", {}, tier=1, category="university"),
                PageContent("https://uetpeshawar.edu.pk/financial-aid/", "UET Peshawar Directorate of Financial Aid", {}, tier=1, category="university"),
                PageContent("https://www.hec.gov.pk/english/scholarshipsgrants/NBS/", "HEC Need Based Scholarships", {}, tier=1, category="federal_govt"),
                PageContent("https://abasyn.edu.pk/scholarships/", "Abasyn University Scholarships", {}, tier=1, category="university"),
                PageContent("https://www.ihsantrust.org/education-loan/", "Ihsan Trust Interest Free Loan", {}, tier=1, category="NGO-foundation"),
                PageContent("https://www.chevening.org/scholarship/pakistan/", "Chevening Scholarships", {}, tier=1, category="international"),
            ]
        else:
            for s in seed_sources:
                url = s.get("url")
                tier = s.get("tier", 1)
                cat = s.get("category", "")
                page = self.fetcher.fetch_url(url=url, tier=tier, category=cat)
                if page:
                    fetched_pages.append(page)
                    # Follow up to follow_links_per_seed sublinks
                    sublinks = self.fetcher.extract_sublinks(page)
                    for sub in sublinks:
                        if sub not in discovered_urls_set:
                            discovered_urls_set.add(sub)
                else:
                    failed_sources.append(url)

        # Check degraded threshold (>50% seed failures)
        degraded = False
        if total_seeds > 0 and (len(failed_sources) / total_seeds) > 0.50:
            degraded = True
            logger.warning(f"DEGRADED MODE ACTIVATED: {len(failed_sources)} of {total_seeds} seed sources failed.")

        # Step 3: Discovery queries via Gemini search grounding
        discovery_queries = self.settings.get("discovery_queries", [])
        max_discovered = self.settings.get("pipeline", {}).get("max_discovered_urls", 25)

        for dq in discovery_queries:
            query = dq.get("query", "")
            focus = dq.get("focus", "")
            items = self.gemini_client.run_discovery_query(
                query=query, focus=focus, today_pkt=today_str, cycle=self.settings.get("cycle", "2026-27"), force_mock=dry_run
            )
            for item in items:
                target_url = item.official_url or item.other_url
                if target_url and target_url.startswith("http") and not self._is_blocked(target_url):
                    discovered_urls_set.add(target_url)

        # Fetch discovered URLs up to max_discovered if not in dry_run
        if not dry_run:
            for disc_url in list(discovered_urls_set)[:max_discovered]:
                if not any(p.url == disc_url for p in fetched_pages):
                    page = self.fetcher.fetch_url(disc_url, tier=2)
                    if page:
                        fetched_pages.append(page)
                    else:
                        failed_sources.append(disc_url)

        logger.info(f"Successfully processed {len(fetched_pages)} pages. Unreachable sources: {len(failed_sources)}")

        # Step 4: Extraction
        extracted_items: List[ScholarshipExtractionItem] = []
        for page in fetched_pages:
            items = self.gemini_client.extract_scholarships_from_page(
                page_text=page.text,
                source_url=page.url,
                tier=page.tier,
                links_map=page.links,
                today_pkt=today_str,
                cycle=self.settings.get("cycle", "2026-27"),
                force_mock=dry_run
            )
            extracted_items.extend(items)

        logger.info(f"Extracted {len(extracted_items)} raw scholarship items from fetched pages.")

        # Step 5: Normalization & Verification
        normalized_new_records: List[ScholarshipRecord] = []
        for item in extracted_items:
            # Check blocklist names
            if any(bn.lower() in item.name.lower() for bn in self.settings.get("blocklist_names", [])):
                continue

            rec = self.normalizer.normalize_record(
                item=item,
                source_tier=item.confirmed_by_official_source and 1 or 2,
                source_url=item.source_url,
                today_date=today_date,
                verify_links=verify_links
            )

            # Re-classify university sector with HEC database (ensuring IMSciences = public)
            classified_sector = self.classifier.classify_university_name(
                f"{rec.eligible_institutions} {rec.sponsor} {rec.name}"
            )
            if classified_sector != "not stated":
                rec.university_types = classified_sector

            # Calculate priority flags
            (
                rec.charsadda_flag,
                rec.kp_flag,
                rec.pakistan_wide_kp_eligible,
                rec.target_uni_flag,
                rec.merged_districts_only
            ) = self.classifier.calculate_priority_flags(rec.model_dump())

            normalized_new_records.append(rec)

        # Step 6: Deduplication & State Merge
        all_active_records = self.deduplicator.deduplicate_and_merge(
            new_records=normalized_new_records,
            previous_records=previous_records,
            today_date=today_date
        )

        # Save merged state back to data/scholarships.json
        self._save_state(state_file, all_active_records)
        logger.info(f"Saved {len(all_active_records)} merged records to {state_file}")

        # Step 7: Split into Public and Private reports
        pub_records, priv_records = self._split_reports(all_active_records)

        # Separate international, watchlist, and closed for both reports
        pub_main, pub_intl, pub_watch, pub_closed = self._partition_records(pub_records, today_date)
        priv_main, priv_intl, priv_watch, priv_closed = self._partition_records(priv_records, today_date)

        # Sort main records: soonest deadline first, priority weighted
        pub_main = self._sort_records(pub_main)
        priv_main = self._sort_records(priv_main)

        # Step 8: Prepare Summaries
        pub_summary = self._compute_summary(
            title="Khyber Pakhtunkhwa Scholarships Intelligence: Public-Sector Universities",
            audience="Public-Sector Universities (UoP, UET Peshawar, BKUC, KMU, AUP, AWKUM, IMSciences*)",
            records=pub_main,
            today_pkt=time_pkt_str,
            run_id=run_id,
            sources_count=len(fetched_pages),
            degraded=degraded,
            today_date_str=today_str
        )

        priv_summary = self._compute_summary(
            title="Khyber Pakhtunkhwa Scholarships Intelligence: Private-Sector Universities",
            audience="Private-Sector Universities (Abasyn University Peshawar, CECOS, INU, CUSIT, SUIT)",
            records=priv_main,
            today_pkt=time_pkt_str,
            run_id=run_id,
            sources_count=len(fetched_pages),
            degraded=degraded,
            today_date_str=today_str
        )

        # Step 9: Render HTML, PDF, XLSX, and CSV
        report_dir = self.reports_dir / today_str
        report_dir.mkdir(parents=True, exist_ok=True)

        generated_files = self._render_all_reports(
            report_dir=report_dir,
            today_str=today_str,
            pub_summary=pub_summary,
            pub_main=pub_main,
            pub_intl=pub_intl,
            pub_watch=pub_watch,
            pub_closed=pub_closed,
            priv_summary=priv_summary,
            priv_main=priv_main,
            priv_intl=priv_intl,
            priv_watch=priv_watch,
            priv_closed=priv_closed,
            failed_sources=failed_sources
        )

        # Step 10: Email reports via Resend (filtered to PDF format only)
        attach_formats = os.environ.get("EMAIL_ATTACHMENT_FORMATS") or self.settings.get("email", {}).get("attachment_formats", "pdf")
        if isinstance(attach_formats, str):
            allowed_exts = {f".{ext.strip().lower().lstrip('.')}" for ext in attach_formats.split(",") if ext.strip()}
        elif isinstance(attach_formats, (list, tuple, set)):
            allowed_exts = {f".{str(ext).strip().lower().lstrip('.')}" for ext in attach_formats}
        else:
            allowed_exts = {".pdf"}

        email_attachments = [f for f in generated_files if f.suffix.lower() in allowed_exts]

        email_sent = self.emailer.send_daily_reports(
            public_summary=pub_summary,
            private_summary=priv_summary,
            attachment_paths=email_attachments,
            degraded=degraded,
            today_pkt=today_str,
            dry_run=dry_run
        )

        return {
            "run_id": run_id,
            "today_pkt": time_pkt_str,
            "degraded": degraded,
            "sources_checked": len(fetched_pages),
            "sources_failed": len(failed_sources),
            "public_opportunities": len(pub_main),
            "private_opportunities": len(priv_main),
            "generated_files": [str(f) for f in generated_files],
            "email_sent": email_sent
        }

    def _split_reports(
        self, records: List[ScholarshipRecord]
    ) -> Tuple[List[ScholarshipRecord], List[ScholarshipRecord]]:
        """Splits opportunities into Public and Private university audiences.
        'not stated' goes into both reports with a warning badge.
        """
        public_list = []
        private_list = []

        for r in records:
            ut = r.university_types
            if ut in ["public", "both"]:
                public_list.append(r)
            elif ut in ["private", "both"]:
                private_list.append(r)
            elif ut == "not stated":
                # Goes to both reports with 'confirm university eligibility' warning
                public_list.append(r)
                private_list.append(r)

        return public_list, private_list

    def _partition_records(
        self, records: List[ScholarshipRecord], today_date: datetime.date
    ) -> Tuple[List[ScholarshipRecord], List[ScholarshipRecord], List[ScholarshipRecord], List[ScholarshipRecord]]:
        """Partitions records into:
        1. Main active
        2. International
        3. Watchlist (previous cycle / awaiting new call)
        4. Recently closed (last 30 days)
        """
        main = []
        intl = []
        watch = []
        closed = []

        for r in records:
            if r.status == "Previous cycle – awaiting new call":
                watch.append(r)
            elif r.status == "Closed":
                # Check if closed within last 30 days
                if r.days_left is not None and -30 <= r.days_left < 0:
                    closed.append(r)
            elif r.sponsor_type == "international":
                intl.append(r)
            else:
                main.append(r)

        return main, intl, watch, closed

    def _sort_records(self, records: List[ScholarshipRecord]) -> List[ScholarshipRecord]:
        """Sorting rule from Section 4:
        Soonest deadline first.
        After that: Rolling, Deadline not stated, Upcoming (by opening date).
        Extra priority weight to Charsadda flag and Target uni flag.
        """
        def sort_key(r: ScholarshipRecord):
            # Status group order:
            # 0: Closing soon & Open (numeric deadline)
            # 1: Rolling / ongoing
            # 2: Deadline not stated
            # 3: Upcoming
            # 4: Other / Closed
            if r.status in ["Closing soon", "Open"]:
                group = 0
                val = r.days_left if r.days_left is not None else 999
            elif r.status == "Rolling / ongoing":
                group = 1
                val = 0
            elif r.status == "Deadline not stated":
                group = 2
                val = 0
            elif r.status == "Upcoming":
                group = 3
                val = r.days_left if r.days_left is not None else 999
            else:
                group = 4
                val = 999

            # Priority boost (Charsadda = -2, Target Uni = -1)
            priority_score = 0
            if r.charsadda_flag:
                priority_score -= 2
            if r.target_uni_flag:
                priority_score -= 1

            return (group, priority_score, val, r.name)

        return sorted(records, key=sort_key)

    def _compute_summary(
        self,
        title: str,
        audience: str,
        records: List[ScholarshipRecord],
        today_pkt: str,
        run_id: str,
        sources_count: int,
        degraded: bool,
        today_date_str: str
    ) -> ReportSummary:
        new_today = sum(1 for r in records if r.first_seen == today_date_str)
        closing_7d = sum(1 for r in records if r.days_left is not None and 0 <= r.days_left <= 7)
        charsadda_count = sum(1 for r in records if r.charsadda_flag)
        kp_count = sum(1 for r in records if r.kp_flag or r.pakistan_wide_kp_eligible)
        broken_links = sum(1 for r in records if r.link_status_apply == "broken" or r.link_status_source == "broken")

        return ReportSummary(
            title=title,
            audience=audience,
            generated_at_pkt=today_pkt,
            run_id=run_id,
            sources_checked_count=sources_count,
            total_opportunities=len(records),
            new_since_yesterday=new_today,
            closing_within_7_days=closing_7d,
            charsadda_eligible_count=charsadda_count,
            kp_eligible_count=kp_count,
            broken_links_count=broken_links,
            degraded_mode=degraded
        )

    def _render_all_reports(
        self,
        report_dir: Path,
        today_str: str,
        pub_summary: ReportSummary,
        pub_main: List[ScholarshipRecord],
        pub_intl: List[ScholarshipRecord],
        pub_watch: List[ScholarshipRecord],
        pub_closed: List[ScholarshipRecord],
        priv_summary: ReportSummary,
        priv_main: List[ScholarshipRecord],
        priv_intl: List[ScholarshipRecord],
        priv_watch: List[ScholarshipRecord],
        priv_closed: List[ScholarshipRecord],
        failed_sources: List[str]
    ) -> List[Path]:
        """Generates HTML, PDF, XLSX, and CSV for both public and private reports."""
        file_paths = []

        # 1. Public Report Files
        pub_html_path = report_dir / f"public_scholarships_report_{today_str}.html"
        pub_pdf_path = report_dir / f"public_scholarships_report_{today_str}.pdf"
        pub_xlsx_path = report_dir / f"public_scholarships_report_{today_str}.xlsx"
        pub_csv_path = report_dir / f"public_scholarships_report_{today_str}.csv"

        pub_html = self.html_gen.generate_report(
            summary=pub_summary,
            main_records=pub_main,
            international_records=pub_intl,
            watchlist_records=pub_watch,
            closed_records=pub_closed,
            unprocessed_sources=failed_sources,
            report_type="public"
        )
        with open(pub_html_path, "w", encoding="utf-8") as f:
            f.write(pub_html)
        file_paths.append(pub_html_path)

        self.pdf_gen.generate_pdf(
            summary=pub_summary,
            main_records=pub_main,
            international_records=pub_intl,
            watchlist_records=pub_watch,
            output_path=pub_pdf_path
        )
        file_paths.append(pub_pdf_path)

        self.excel_gen.generate_excel(
            summary=pub_summary,
            main_records=pub_main,
            international_records=pub_intl,
            watchlist_records=pub_watch,
            output_path=pub_xlsx_path
        )
        file_paths.append(pub_xlsx_path)

        self.csv_gen.generate_csv(pub_main + pub_intl, pub_csv_path)
        file_paths.append(pub_csv_path)

        # 2. Private Report Files
        priv_html_path = report_dir / f"private_scholarships_report_{today_str}.html"
        priv_pdf_path = report_dir / f"private_scholarships_report_{today_str}.pdf"
        priv_xlsx_path = report_dir / f"private_scholarships_report_{today_str}.xlsx"
        priv_csv_path = report_dir / f"private_scholarships_report_{today_str}.csv"

        priv_html = self.html_gen.generate_report(
            summary=priv_summary,
            main_records=priv_main,
            international_records=priv_intl,
            watchlist_records=priv_watch,
            closed_records=priv_closed,
            unprocessed_sources=failed_sources,
            report_type="private"
        )
        with open(priv_html_path, "w", encoding="utf-8") as f:
            f.write(priv_html)
        file_paths.append(priv_html_path)

        self.pdf_gen.generate_pdf(
            summary=priv_summary,
            main_records=priv_main,
            international_records=priv_intl,
            watchlist_records=priv_watch,
            output_path=priv_pdf_path
        )
        file_paths.append(priv_pdf_path)

        self.excel_gen.generate_excel(
            summary=priv_summary,
            main_records=priv_main,
            international_records=priv_intl,
            watchlist_records=priv_watch,
            output_path=priv_xlsx_path
        )
        file_paths.append(priv_xlsx_path)

        self.csv_gen.generate_csv(priv_main + priv_intl, priv_csv_path)
        file_paths.append(priv_csv_path)

        logger.info(f"Successfully rendered 8 report files in {report_dir}")
        return file_paths

    def _is_blocked(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        blocklist = self.settings.get("blocklist_domains", [])
        return any(bd.lower() in domain for bd in blocklist)

    def _load_state(self, path: Path) -> List[ScholarshipRecord]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [ScholarshipRecord(**item) for item in data]
        except Exception as e:
            logger.warning(f"Failed to load state from {path}: {e}")
            return []

    def _save_state(self, path: Path, records: List[ScholarshipRecord]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                data = [r.model_dump() for r in records]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save state to {path}: {e}")
