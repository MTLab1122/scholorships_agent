"""Agent 14: Source Coverage and Performance Agent
Aggregates operational telemetry across research sources, discovery runs,
verification success rates, duplicate occurrences, and API usage.
Generates administrative health audits for ongoing system reliability.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from agent.db import OpportunityDB


class SourceCoverageAgent:
    """Specialized Agent for monitoring source vitality and system operational health."""

    def __init__(self, db: Optional[OpportunityDB] = None):
        self.db = db or OpportunityDB()

    def generate_system_health_report(self) -> Dict[str, Any]:
        """Synthesizes comprehensive telemetry across opportunities, sources, and execution history."""
        opportunities = self.db.list_opportunities()
        sources = self.db.list_sources()

        # Opportunities breakdown
        total_opps = len(opportunities)
        verified_count = sum(1 for o in opportunities if o.confirmed_by_official_source)
        open_count = sum(1 for o in opportunities if o.status in ["Open", "Rolling / ongoing"])
        closing_soon_count = sum(1 for o in opportunities if o.status == "Closing soon")
        closed_count = sum(1 for o in opportunities if o.status in ["Closed", "Previous cycle – awaiting new call"])
        broken_links_count = sum(1 for o in opportunities if o.link_status_apply == "broken" or o.link_status_source == "broken")

        # Category distribution
        category_distribution: Dict[str, int] = {}
        for o in opportunities:
            cat = o.category or "scholarships"
            category_distribution[cat] = category_distribution.get(cat, 0) + 1

        # Domicile & sector metrics
        kp_eligible_count = sum(1 for o in opportunities if o.kp_eligibility == "yes" or o.charsadda_eligibility == "yes")
        charsadda_count = sum(1 for o in opportunities if o.charsadda_eligibility == "yes")
        public_sector_count = sum(1 for o in opportunities if o.university_types in ["public", "both"])
        private_sector_count = sum(1 for o in opportunities if o.university_types in ["private", "both"])

        # Sources coverage
        total_sources = len(sources)
        active_sources = sum(1 for s in sources if s.get("status") == "active")
        source_types: Dict[str, int] = {}
        for s in sources:
            stype = s.get("source_type") or "portal"
            source_types[stype] = source_types.get(stype, 0) + 1

        # Recent change events and audit logs
        recent_changes = self.db.list_changes(limit=25)
        recent_reports = self.db.list_reports_history(limit=25)

        # Estimated compute/API costs (deterministic calculation based on opportunity count and extractions)
        estimated_input_tokens = total_opps * 850
        estimated_output_tokens = total_opps * 320
        # Gemini 2.5 Flash pricing: ~$0.075 / 1M input tokens, ~$0.30 / 1M output tokens
        estimated_cost_usd = round(
            (estimated_input_tokens / 1_000_000 * 0.075) + (estimated_output_tokens / 1_000_000 * 0.30),
            4
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_system_status": "healthy" if broken_links_count == 0 else "needs_attention",
            "opportunity_metrics": {
                "total_cataloged": total_opps,
                "verified_by_official_source": verified_count,
                "verification_rate_pct": round((verified_count / max(total_opps, 1)) * 100, 1),
                "open_count": open_count,
                "closing_soon_count": closing_soon_count,
                "closed_count": closed_count,
                "broken_links_count": broken_links_count,
                "kp_domicile_opportunities": kp_eligible_count,
                "charsadda_priority_opportunities": charsadda_count,
                "public_university_eligible": public_sector_count,
                "private_university_eligible": private_sector_count,
            },
            "category_breakdown": category_distribution,
            "source_registry_metrics": {
                "total_configured_sources": total_sources,
                "active_sources": active_sources,
                "sources_by_type": source_types,
            },
            "telemetry_and_audits": {
                "recent_change_events_logged": len(recent_changes),
                "recent_reports_generated": len(recent_reports),
                "estimated_tokens_processed": estimated_input_tokens + estimated_output_tokens,
                "estimated_api_cost_usd": estimated_cost_usd
            }
        }
