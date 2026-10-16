"""Deduplication and state merging module.
Merges records with the same sponsor and fuzzy ratio >= 0.88 or the same apply URL.
Preserves earliest first_seen, updates last_verified, retains all source URLs,
and applies the drop_after_days_unseen retention policy.
"""

import difflib
import datetime
from typing import List, Dict, Tuple, Optional
from agent.models import ScholarshipRecord


def compute_fuzzy_ratio(s1: str, s2: str) -> float:
    """Computes string similarity ratio between 0.0 and 1.0."""
    return difflib.SequenceMatcher(None, s1.strip().lower(), s2.strip().lower()).ratio()


class ScholarshipDeduplicator:
    def __init__(self, fuzzy_threshold: float = 0.88, drop_after_days_unseen: int = 30):
        self.fuzzy_threshold = fuzzy_threshold
        self.drop_after_days_unseen = drop_after_days_unseen

    def deduplicate_and_merge(
        self,
        new_records: List[ScholarshipRecord],
        previous_records: List[ScholarshipRecord],
        today_date: datetime.date
    ) -> List[ScholarshipRecord]:
        """Merges today's new records with stored historical records.
        Updates first_seen, last_verified, is_reconfirmed_today, and drops stale records.
        """
        today_str = today_date.strftime("%Y-%m-%d")
        merged_pool: List[ScholarshipRecord] = []

        # 1. Start with today's new records
        for new_rec in new_records:
            matched_idx = self._find_matching_record_index(new_rec, merged_pool)
            if matched_idx is not None:
                merged_pool[matched_idx] = self._merge_two_records(
                    merged_pool[matched_idx], new_rec, is_today=True, today_str=today_str
                )
            else:
                new_rec.is_reconfirmed_today = True
                new_rec.last_verified = today_str
                if not new_rec.first_seen:
                    new_rec.first_seen = today_str
                merged_pool.append(new_rec)

        # 2. Merge previous days' records
        for prev_rec in previous_records:
            matched_idx = self._find_matching_record_index(prev_rec, merged_pool)
            if matched_idx is not None:
                # Matched with a record confirmed today!
                # Update first_seen to earlier date
                current = merged_pool[matched_idx]
                if prev_rec.first_seen and (not current.first_seen or prev_rec.first_seen < current.first_seen):
                    current.first_seen = prev_rec.first_seen
                # Combine source URLs
                for u in prev_rec.all_source_urls:
                    if u not in current.all_source_urls:
                        current.all_source_urls.append(u)
            else:
                # Not reconfirmed today. Check retention age.
                days_unseen = self._calculate_days_unseen(prev_rec.last_verified, today_date)
                if days_unseen <= self.drop_after_days_unseen:
                    # Keep record, mark not re-confirmed today
                    prev_rec.is_reconfirmed_today = False
                    merged_pool.append(prev_rec)

        # Assign unique deterministic IDs
        for idx, rec in enumerate(merged_pool, start=1):
            rec.id = f"SCH-{today_date.strftime('%Y%m')}-{idx:04d}"

        return merged_pool

    def _find_matching_record_index(
        self, candidate: ScholarshipRecord, existing_list: List[ScholarshipRecord]
    ) -> Optional[int]:
        """Finds index of matching record based on apply_url or sponsor + fuzzy name."""
        cand_apply = candidate.apply_url.strip().lower()
        cand_name = candidate.name.strip().lower()
        cand_sponsor = candidate.sponsor.strip().lower()

        for idx, existing in enumerate(existing_list):
            exist_apply = existing.apply_url.strip().lower()
            exist_name = existing.name.strip().lower()
            exist_sponsor = existing.sponsor.strip().lower()

            # Direct apply URL match (if not 'not stated')
            if cand_apply != "not stated" and exist_apply != "not stated" and cand_apply == exist_apply:
                return idx

            # Sponsor similarity & name fuzzy ratio
            sponsor_sim = compute_fuzzy_ratio(cand_sponsor, exist_sponsor)
            if sponsor_sim >= 0.80 or cand_sponsor in exist_sponsor or exist_sponsor in cand_sponsor:
                name_sim = compute_fuzzy_ratio(cand_name, exist_name)
                if name_sim >= self.fuzzy_threshold:
                    return idx

        return None

    def _merge_two_records(
        self, rec1: ScholarshipRecord, rec2: ScholarshipRecord, is_today: bool, today_str: str
    ) -> ScholarshipRecord:
        """Merges two records, keeping the most authoritative value for each field."""
        # rec1 is existing, rec2 is incoming
        primary = rec1 if rec1.source_trust_tier <= rec2.source_trust_tier else rec2
        secondary = rec2 if primary is rec1 else rec1

        merged_dict = primary.model_dump()

        # For any field in primary that is 'not stated' or empty, use secondary's value
        for key, val in secondary.model_dump().items():
            current_val = merged_dict.get(key)
            if (current_val in ["not stated", "", None]) and (val not in ["not stated", "", None]):
                merged_dict[key] = val

        # Retain all source URLs
        urls = list(dict.fromkeys(rec1.all_source_urls + rec2.all_source_urls + [rec1.source_url, rec2.source_url]))
        merged_dict["all_source_urls"] = [u for u in urls if u and u != "not stated"]

        # Date handling
        dates = [d for d in [rec1.first_seen, rec2.first_seen] if d]
        merged_dict["first_seen"] = min(dates) if dates else today_str
        merged_dict["last_verified"] = today_str if is_today else max(filter(None, [rec1.last_verified, rec2.last_verified]), default=today_str)
        merged_dict["is_reconfirmed_today"] = is_today

        # Flags: or-logic
        merged_dict["charsadda_flag"] = rec1.charsadda_flag or rec2.charsadda_flag
        merged_dict["kp_flag"] = rec1.kp_flag or rec2.kp_flag
        merged_dict["pakistan_wide_kp_eligible"] = rec1.pakistan_wide_kp_eligible or rec2.pakistan_wide_kp_eligible
        merged_dict["target_uni_flag"] = rec1.target_uni_flag or rec2.target_uni_flag
        merged_dict["merged_districts_only"] = rec1.merged_districts_only or rec2.merged_districts_only

        return ScholarshipRecord(**merged_dict)

    def _calculate_days_unseen(self, last_verified_str: str, today: datetime.date) -> int:
        if not last_verified_str:
            return 999
        try:
            parts = [int(p) for p in last_verified_str.split("-")]
            last_date = datetime.date(parts[0], parts[1], parts[2])
            return (today - last_date).days
        except Exception:
            return 999
