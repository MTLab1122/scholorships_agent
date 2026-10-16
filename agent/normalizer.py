"""Normalizer module for dates, currency cycles, status, trust tiers, and link verification.
"""

import re
import datetime
from urllib.parse import urlparse
from typing import Optional, Tuple
import requests
from agent.models import (
    ScholarshipExtractionItem,
    ScholarshipRecord,
    OpportunityStatus,
    LinkStatus
)

DATE_REGEX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

TIER_1_DOMAINS = [
    ".gov.pk",
    ".edu.pk",
    "hec.gov.pk",
    "ehsaas.hec.gov.pk",
    "ef.kp.gov.pk",
    "scholarships.kpitb.online",
    "ihsantrust.org",
    "chevening.org",
    "usefp.org",
    "daad.pk",
    "turkiyeburslari.gov.tr",
    "cscuk.fcdo.gov.uk",
    "ogdcl.com",
    "ppl.com.pk",
    "mol.ca",
    "sngpl.com.pk",
    "akhuwat.org.pk",
    "pbm.gov.pk"
]


class OpportunityNormalizer:
    def __init__(self, current_cycle: str = "2026-27", user_agent: str = "ScholarshipVerificationAgent/1.0", timeout: int = 15):
        self.current_cycle = current_cycle
        self.user_agent = user_agent
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "*/*"
        })

    def normalize_record(
        self,
        item: ScholarshipExtractionItem,
        source_tier: int,
        source_url: str,
        today_date: datetime.date,
        verify_links: bool = True
    ) -> ScholarshipRecord:
        """Converts raw extraction item into a normalized, verified ScholarshipRecord."""
        record_dict = item.model_dump()

        # 1. Determine Trust Tier and Verification Badge
        tier = self._assign_tier_from_url(source_url, source_tier)
        if item.confirmed_by_official_source:
            if tier == 1:
                badge = "Confirmed"
            elif tier == 2:
                badge = "Via Partner"
            else:
                badge = "Unverified"
        else:
            badge = "Unverified"

        claimed_by = None
        if badge == "Unverified" and tier == 3:
            claimed_by = source_url

        # 2. Parse Dates & Status
        status, days_left = self._calculate_status_and_days(
            deadline_str=item.deadline,
            opening_str=item.opening_date,
            cycle_str=item.cycle,
            today=today_date
        )

        # 3. Currency / Cycle Check
        # If call belongs to an earlier cycle (e.g. 2024 or 2025 when current is 2026-27)
        if self._is_previous_cycle(item.cycle, item.deadline, today_date):
            status = "Previous cycle – awaiting new call"

        # 4. Link Verification
        apply_status = "not stated"
        source_status = "not stated"
        if verify_links:
            if item.apply_url and item.apply_url != "not stated" and item.apply_url.startswith("http"):
                apply_status = self.check_link(item.apply_url)
            if source_url and source_url != "not stated" and source_url.startswith("http"):
                source_status = self.check_link(source_url)

        # 5. Build Record
        today_str = today_date.strftime("%Y-%m-%d")
        record = ScholarshipRecord(
            **record_dict,
            id="", # Will be set by deduplicator
            status=status,
            days_left=days_left,
            source_trust_tier=tier,
            verification_badge=badge,
            claimed_by_source=claimed_by,
            link_status_apply=apply_status,
            link_status_source=source_status,
            first_seen=today_str,
            last_verified=today_str,
            is_reconfirmed_today=True,
            all_source_urls=[source_url] if source_url and source_url != "not stated" else []
        )

        return record

    def _assign_tier_from_url(self, url: str, suggested_tier: int) -> int:
        if not url or url == "not stated":
            return suggested_tier
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for t1 in TIER_1_DOMAINS:
            if t1 in domain:
                return 1

        return suggested_tier

    def _calculate_status_and_days(
        self,
        deadline_str: str,
        opening_str: str,
        cycle_str: str,
        today: datetime.date
    ) -> Tuple[OpportunityStatus, Optional[int]]:
        """Calculates status based on today's PKT date."""
        low_dead = (deadline_str or "").strip().lower()
        low_open = (opening_str or "").strip().lower()

        # Check for rolling/ongoing
        if "rolling" in low_dead or "ongoing" in low_dead or "continuous" in low_dead or "open always" in low_dead:
            return "Rolling / ongoing", None

        # Check for Upcoming based on opening date
        match_open = DATE_REGEX.match(opening_str.strip()) if opening_str else None
        if match_open:
            try:
                open_date = datetime.date(int(match_open.group(1)), int(match_open.group(2)), int(match_open.group(3)))
                if open_date > today:
                    return "Upcoming", (open_date - today).days
            except ValueError:
                pass

        # Check deadline date
        match_dead = DATE_REGEX.match(deadline_str.strip()) if deadline_str else None
        if match_dead:
            try:
                dead_date = datetime.date(int(match_dead.group(1)), int(match_dead.group(2)), int(match_dead.group(3)))
                days_left = (dead_date - today).days

                if days_left < 0:
                    return "Closed", days_left
                elif days_left <= 7:
                    return "Closing soon", days_left
                else:
                    return "Open", days_left
            except ValueError:
                pass

        if low_dead in ["not stated", "", "none"]:
            return "Deadline not stated", None

        # If fuzzy text in deadline mentions closed
        if "closed" in low_dead or "expired" in low_dead:
            return "Closed", None

        return "Deadline not stated", None

    def _is_previous_cycle(self, cycle_str: str, deadline_str: str, today: datetime.date) -> bool:
        """Determines if the announcement is from an earlier academic year/cycle."""
        combined = f"{cycle_str} {deadline_str}".lower()
        current_year = today.year

        # If it explicitly mentions years prior to current year - 1
        for past_year in range(2015, current_year - 1):
            if str(past_year) in combined and str(current_year) not in combined:
                return True

        return False

    def check_link(self, url: str) -> LinkStatus:
        """Sends an HTTP GET to verify link status following redirects.
        Status < 400 -> working, 4xx/5xx -> broken, timeout -> unreachable.
        """
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code < 400:
                return "working"
            else:
                return "broken"
        except requests.exceptions.Timeout:
            return "unreachable"
        except requests.exceptions.RequestException:
            return "broken"
        except Exception:
            return "unreachable"
