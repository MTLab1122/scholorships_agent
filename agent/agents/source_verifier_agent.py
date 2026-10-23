"""Agent 5: Official-Source Verification Agent.
Verifies opportunities against authoritative domains (*.gov.pk, *.edu.pk, verified sponsor portals).
Separates source authenticity, link status, and deadline currency into verifiable indicators.
Never marks an opportunity as verified solely based on AI confidence.
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from agent.normalizer import OpportunityNormalizer, LinkStatus
from agent.models import ScholarshipRecord

logger = logging.getLogger(__name__)

TIER_1_PATTERNS = [
    ".gov.pk",
    ".edu.pk",
    "hec.gov.pk",
    "ef.kp.gov.pk",
    "kpitb.online",
    "chevening.org",
    "usefp.org",
    "daad.de",
    "turkiyeburslari.gov.tr",
    "cern.ch",
    "pseb.org.pk",
    "ignite.org.pk"
]


class SourceVerificationAgent:
    def __init__(self, normalizer: Optional[OpportunityNormalizer] = None):
        self.normalizer = normalizer or OpportunityNormalizer()

    def verify_opportunity(
        self,
        record: ScholarshipRecord,
        today_date: Optional[Any] = None,
        verify_links: bool = True
    ) -> ScholarshipRecord:
        """Runs link checks, domain authenticity check, and deadline calculation."""
        import datetime
        today = today_date or datetime.date.today()

        # 1. Domain Authenticity & Trust Tier
        record.source_trust_tier = self._compute_trust_tier(record.source_url, record.apply_url)
        if record.source_trust_tier == 1:
            record.verification_badge = "Confirmed"
            record.confirmed_by_official_source = True
        elif record.source_trust_tier == 2:
            record.verification_badge = "Via Partner"
            record.confirmed_by_official_source = True
        else:
            record.verification_badge = "Unverified"
            record.confirmed_by_official_source = False

        # 2. HTTP Link Verification
        if verify_links:
            if record.apply_url and record.apply_url != "not stated":
                record.link_status_apply = self.normalizer.check_link(record.apply_url)
            else:
                record.link_status_apply = "not stated"

            if record.source_url and record.source_url != "not stated":
                record.link_status_source = self.normalizer.check_link(record.source_url)
            else:
                record.link_status_source = "not stated"

        # 3. Deadline & Status Computation
        status, days_left = self.normalizer.compute_status(
            deadline_str=record.deadline,
            opening_str=record.opening_date,
            expiry_str=record.expiry_date,
            cycle_str=record.cycle,
            today=today
        )
        record.status = status
        record.days_left = days_left
        record.last_verified = today.strftime("%Y-%m-%d")

        return record

    def _compute_trust_tier(self, source_url: str, apply_url: str) -> int:
        urls_to_check = [u.lower() for u in [source_url, apply_url] if u and u != "not stated"]
        for u in urls_to_check:
            for pattern in TIER_1_PATTERNS:
                if pattern in u:
                    return 1

        # Check for edu or partner domains
        for u in urls_to_check:
            host = urlparse(u).netloc
            if host.endswith(".org") or host.endswith(".edu"):
                return 2

        return 3

    def verify(self, record: ScholarshipRecord) -> Dict[str, Any]:
        """Convenience verification method returning verification status dict."""
        updated_rec = self.verify_opportunity(record, verify_links=False)
        return {
            "is_verified": updated_rec.confirmed_by_official_source,
            "trust_tier": updated_rec.source_trust_tier,
            "verification_badge": updated_rec.verification_badge,
            "status": updated_rec.status,
            "days_left": updated_rec.days_left,
            "record": updated_rec
        }


# Alias for naming consistency across specs
OfficialSourceVerificationAgent = SourceVerificationAgent

