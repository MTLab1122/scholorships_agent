"""Agent 13: Fraud and Quality-Control Agent
Inspects opportunity records for red flags, non-official payment demands,
suspicious fee collection (EasyPaisa/JazzCash), domain spoofing, guaranteed admission claims,
and broken/unsupported links. Routes risky records to human admin review.
"""

import re
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
from agent.models import OpportunityRecord


# Known official Pakistan higher education domain suffixes
OFFICIAL_SUFFIXES = [
    ".gov.pk",
    ".edu.pk",
    ".org.pk",
    ".ac.uk",
    ".edu",
    ".org",
    ".unesco.org",
    ".daad.de",
    ".chevening.org",
    ".fulbrightprogram.org"
]

# Suspicious words indicative of fee scams or false promises
SUSPICIOUS_KEYWORDS = [
    "100% guaranteed",
    "guaranteed selection",
    "guaranteed visa",
    "pay processing fee via easypaisa",
    "send money to jazzcash",
    "western union",
    "direct cash payment",
    "whatsapp only application",
    "secret selection list",
    "agent commission",
]

SUSPICIOUS_DOMAINS = [
    "blogspot.com",
    "wordpress.com",
    "wixsite.com",
    "weebly.com",
    "tinyurl.com",
    "bit.ly",
    "cutt.ly"
]


class FraudAndQCAgent:
    """Specialized Agent for fraud mitigation, source veracity, and quality assurance."""

    def __init__(self):
        pass

    def evaluate_opportunity(self, opp: OpportunityRecord) -> Dict[str, Any]:
        """Performs rigorous multi-factor fraud and quality inspection on an opportunity record."""
        flags: List[str] = []
        risk_score = 0.0

        text_to_check = f"{opp.name} {opp.application_procedure} {opp.award_amount} {opp.benefits} {opp.other_conditions}".lower()

        # 1. Check for scam and fee keywords
        for kw in SUSPICIOUS_KEYWORDS:
            if kw in text_to_check:
                flags.append(f"Suspicious phrasing detected: '{kw}'")
                risk_score += 0.40

        # 2. Check for private mobile wallet payment solicitations
        if re.search(r"(easypaisa|jazzcash|omni|upaisa)\s*(account|number|transfer)", text_to_check):
            flags.append("Demands fee payment via private mobile wallet (EasyPaisa/JazzCash)")
            risk_score += 0.50

        # 3. Check for free hosting / suspicious blogging platforms claiming to be official sponsors
        target_url = opp.apply_url or opp.source_url or ""
        parsed_url = urlparse(target_url)
        netloc = parsed_url.netloc.lower()

        for susp_domain in SUSPICIOUS_DOMAINS:
            if susp_domain in netloc:
                flags.append(f"Opportunity uses free blogging/shortener domain ({susp_domain}) instead of institutional portal")
                risk_score += 0.25

        # 4. Check for official claim without official domain
        if opp.sponsor_type in ["federal govt", "provincial govt", "university"]:
            is_official_domain = any(netloc.endswith(suffix) or f".{suffix}." in netloc for suffix in [".gov.pk", ".edu.pk", ".edu", ".org"])
            if not is_official_domain and netloc:
                flags.append(f"Claims '{opp.sponsor_type}' identity but URL host '{netloc}' does not match official .gov.pk / .edu.pk registry")
                risk_score += 0.20

        # 5. Check for missing evidence quote
        if not opp.evidence_quote or opp.evidence_quote.strip() == "":
            flags.append("Missing verbatim official evidence quote")
            risk_score += 0.15

        # 6. Check for expired dates marked as Open
        if opp.status == "Open" and opp.days_left is not None and opp.days_left < 0:
            flags.append("Quality Error: Record has status 'Open' but deadline date is in the past")
            risk_score += 0.30

        # 7. Check for unverified links
        if opp.link_status_apply == "broken" or opp.link_status_source == "broken":
            flags.append("Broken official application link")
            risk_score += 0.20

        # Cap score between 0.0 and 1.0
        risk_score = min(max(round(risk_score, 2), 0.0), 1.0)

        # Severity categorization
        if risk_score >= 0.60:
            severity = "critical"
            requires_admin_review = True
        elif risk_score >= 0.35:
            severity = "high"
            requires_admin_review = True
        elif risk_score >= 0.15:
            severity = "medium"
            requires_admin_review = False
        else:
            severity = "low"
            requires_admin_review = False

        return {
            "opportunity_id": opp.id,
            "opportunity_name": opp.name,
            "risk_score": risk_score,
            "severity": severity,
            "requires_admin_review": requires_admin_review,
            "flags": flags,
            "is_trusted": risk_score < 0.35
        }

    def batch_audit(self, records: List[OpportunityRecord]) -> Dict[str, Any]:
        """Audits a collection of opportunities and summarizes security health."""
        flagged_records = []
        clean_count = 0
        total_risk = 0.0

        for r in records:
            res = self.evaluate_opportunity(r)
            total_risk += res["risk_score"]
            if res["flags"]:
                flagged_records.append(res)
            else:
                clean_count += 1

        avg_risk = round(total_risk / max(len(records), 1), 3)

        return {
            "total_inspected": len(records),
            "clean_count": clean_count,
            "flagged_count": len(flagged_records),
            "average_risk_score": avg_risk,
            "flagged_opportunities": flagged_records
        }
