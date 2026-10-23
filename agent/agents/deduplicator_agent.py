"""Agent 6: Deduplication and Change Detection Agent.
Merges duplicates across multiple crawls and discovery sources.
Records historical changes (deadlines, requirements, funding amounts, links)
into database without losing original source provenance.
"""

import difflib
import datetime
import logging
from typing import List, Dict, Any, Optional, Tuple
from agent.models import ScholarshipRecord
from agent.db import Database

logger = logging.getLogger(__name__)


def compute_similarity(s1: str, s2: str) -> float:
    return difflib.SequenceMatcher(None, s1.strip().lower(), s2.strip().lower()).ratio()


class DeduplicationAndChangeAgent:
    def __init__(
        self,
        fuzzy_threshold: float = 0.88,
        drop_after_days_unseen: int = 30,
        db: Optional[Database] = None
    ):
        self.fuzzy_threshold = fuzzy_threshold
        self.drop_after_days_unseen = drop_after_days_unseen
        self.db = db

    def deduplicate_and_detect_changes(
        self,
        new_records: List[ScholarshipRecord],
        previous_records: List[ScholarshipRecord],
        today_date: datetime.date
    ) -> List[ScholarshipRecord]:
        """Merges new records with stored pool, recording material changes."""
        today_str = today_date.strftime("%Y-%m-%d")
        merged_pool: List[ScholarshipRecord] = []

        # 1. Process today's records
        for new_rec in new_records:
            match_idx = self._find_match(new_rec, merged_pool)
            if match_idx is not None:
                merged_pool[match_idx] = self._merge_two(
                    merged_pool[match_idx], new_rec, is_today=True, today_str=today_str
                )
            else:
                new_rec.is_reconfirmed_today = True
                new_rec.last_verified = today_str
                if not new_rec.first_seen:
                    new_rec.first_seen = today_str
                merged_pool.append(new_rec)

        # 2. Process historical stored records
        for prev_rec in previous_records:
            match_idx = self._find_match(prev_rec, merged_pool)
            if match_idx is not None:
                current = merged_pool[match_idx]
                # Preserve existing persistent ID
                if prev_rec.id:
                    current.id = prev_rec.id

                # Detect changes between prev_rec and current
                if self.db:
                    if prev_rec.deadline != current.deadline and current.deadline not in ["", "not stated"]:
                        self.db.record_change(
                            current.id, "deadline_change", "deadline",
                            prev_rec.deadline, current.deadline, today_str
                        )
                    if prev_rec.award_amount != current.award_amount and current.award_amount not in ["", "not stated"]:
                        self.db.record_change(
                            current.id, "award_amount_change", "award_amount",
                            prev_rec.award_amount, current.award_amount, today_str
                        )

                if prev_rec.first_seen and (not current.first_seen or prev_rec.first_seen < current.first_seen):
                    current.first_seen = prev_rec.first_seen

                # Merge all URLs from both records
                for u in [prev_rec.source_url, prev_rec.apply_url] + prev_rec.all_source_urls:
                    if u and u != "not stated" and u not in current.all_source_urls:
                        current.all_source_urls.append(u)
                for u in [current.source_url, current.apply_url]:
                    if u and u != "not stated" and u not in current.all_source_urls:
                        current.all_source_urls.append(u)

                # Preserve fields from prev_rec if current is empty or "not stated"
                for field in [
                    "category", "university_types", "eligible_institutions", "degree_levels",
                    "fields_of_study", "academic_years", "domicile_requirements", "district_requirements",
                    "kp_eligibility", "charsadda_eligibility", "award_amount", "benefits",
                    "min_gpa_or_marks", "income_cap", "application_procedure", "required_documents",
                    "evidence_quote", "eligible_semesters", "charsadda_flag", "kp_flag", "target_uni_flag"
                ]:
                    cur_val = getattr(current, field, None)
                    prev_val = getattr(prev_rec, field, None)
                    if (cur_val is None or cur_val == "not stated" or cur_val == []) and prev_val not in [None, "not stated", []]:
                        setattr(current, field, prev_val)

                if not current.notes and prev_rec.notes:
                    current.notes = prev_rec.notes
            else:
                # Unseen today - check retention policy
                prev_rec.is_reconfirmed_today = False
                last_ver = prev_rec.last_verified or prev_rec.first_seen or today_str
                try:
                    last_date = datetime.datetime.strptime(last_ver, "%Y-%m-%d").date()
                    days_unseen = (today_date - last_date).days
                except Exception:
                    days_unseen = 0

                if days_unseen <= self.drop_after_days_unseen:
                    # Also ensure prev_rec URLs are collected
                    for u in [prev_rec.source_url, prev_rec.apply_url]:
                        if u and u != "not stated" and u not in prev_rec.all_source_urls:
                            prev_rec.all_source_urls.append(u)
                    merged_pool.append(prev_rec)
                else:
                    logger.info(f"Deduplicator: Dropping obsolete record '{prev_rec.name}' unseen for {days_unseen} days.")

        # Sync to DB if DB is active
        if self.db:
            for rec in merged_pool:
                try:
                    self.db.save_opportunity(rec.model_dump())
                except Exception as e:
                    logger.debug(f"DB save error in deduplicator: {e}")

        return merged_pool

    def _sponsors_match(self, s1: str, s2: str) -> bool:
        c1 = (s1 or "").strip().lower().replace("(", "").replace(")", "").replace("-", " ")
        c2 = (s2 or "").strip().lower().replace("(", "").replace(")", "").replace("-", " ")
        if not c1 or not c2:
            return True
        if c1 == c2 or c1 in c2 or c2 in c1:
            return True
        words1 = [w[0] for w in c1.split() if w]
        words2 = [w[0] for w in c2.split() if w]
        if "".join(words1) == c2 or "".join(words2) == c1:
            return True
        return compute_similarity(c1, c2) >= 0.70

    def _find_match(self, target: ScholarshipRecord, pool: List[ScholarshipRecord]) -> Optional[int]:
        # 1. Direct ID match
        if target.id and target.id != "not stated":
            for i, item in enumerate(pool):
                if item.id and item.id == target.id:
                    return i

        # 2. Direct Apply URL match
        if target.apply_url and target.apply_url != "not stated":
            for i, item in enumerate(pool):
                if item.apply_url and item.apply_url != "not stated" and item.apply_url.strip().lower() == target.apply_url.strip().lower():
                    return i

        # 3. Direct Source URL match
        if target.source_url and target.source_url != "not stated":
            for i, item in enumerate(pool):
                if item.source_url and item.source_url != "not stated" and item.source_url.strip().lower() == target.source_url.strip().lower():
                    return i

        # 4. Sponsor + Name fuzzy match
        for i, item in enumerate(pool):
            sim_name = compute_similarity(item.name, target.name)
            if sim_name >= 0.90:
                return i
            if sim_name >= self.fuzzy_threshold and self._sponsors_match(item.sponsor, target.sponsor):
                return i

        return None

    def _merge_two(
        self,
        existing: ScholarshipRecord,
        incoming: ScholarshipRecord,
        is_today: bool,
        today_str: str
    ) -> ScholarshipRecord:
        """Merges two records and records changes into database."""
        # Detect field differences
        if self.db:
            if existing.deadline != incoming.deadline and incoming.deadline not in ["", "not stated"]:
                self.db.record_change(
                    existing.id or incoming.id, "deadline_change", "deadline",
                    existing.deadline, incoming.deadline, today_str
                )
            if existing.award_amount != incoming.award_amount and incoming.award_amount not in ["", "not stated"]:
                self.db.record_change(
                    existing.id or incoming.id, "award_amount_change", "award_amount",
                    existing.award_amount, incoming.award_amount, today_str
                )

        # Merge authority: prefer incoming if higher tier or non-empty
        if incoming.source_trust_tier <= existing.source_trust_tier:
            for field in [
                "deadline", "award_amount", "benefits", "apply_url", "min_gpa_or_marks",
                "income_cap", "application_procedure", "required_documents", "evidence_quote"
            ]:
                val = getattr(incoming, field, "not stated")
                if val and val != "not stated":
                    setattr(existing, field, val)

        if incoming.status in ["Closing soon", "Open", "Upcoming"]:
            existing.status = incoming.status
            existing.days_left = incoming.days_left

        if is_today:
            existing.is_reconfirmed_today = True
            existing.last_verified = today_str

        # Combine URLs
        for u in [incoming.source_url, incoming.apply_url] + incoming.all_source_urls:
            if u and u != "not stated" and u not in existing.all_source_urls:
                existing.all_source_urls.append(u)
        for u in [existing.source_url, existing.apply_url]:
            if u and u != "not stated" and u not in existing.all_source_urls:
                existing.all_source_urls.append(u)

        return existing

    def process_new_records(self, new_records: List[ScholarshipRecord]) -> Dict[str, Any]:
        """Convenience method for orchestrator to process new records against existing DB records."""
        existing_records = self.db.list_opportunities() if self.db else []
        today = datetime.date.today()
        merged = self.deduplicate_and_detect_changes(new_records, existing_records, today)
        
        # Save merged records back to DB if DB is present
        saved_count = 0
        if self.db:
            for rec in merged:
                self.db.save_opportunity(rec.model_dump())
                saved_count += 1

        return {
            "incoming_count": len(new_records),
            "merged_count": len(merged),
            "saved_to_db": saved_count
        }


# Alias for naming consistency across specifications
DeduplicationAndChangeDetectionAgent = DeduplicationAndChangeAgent

