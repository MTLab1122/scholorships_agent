"""Agent 1: Opportunity Discovery Agent.
Discovers new opportunity announcements across registered government portals,
HEC, university websites, internship providers, research institutes, and foundations.
Supports both live Google Search grounding queries via Gemini client and static seed crawling.
"""

import logging
from typing import List, Dict, Any, Optional
from agent.models import DiscoveryItem
from agent.fetcher import ContentFetcher, PageContent
from agent.gemini_client import GeminiScholarshipClient

logger = logging.getLogger(__name__)


class OpportunityDiscoveryAgent:
    def __init__(
        self,
        gemini_client: Optional[GeminiScholarshipClient] = None,
        fetcher: Optional[ContentFetcher] = None,
        sources_cfg: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None
    ):
        self.gemini_client = gemini_client
        self.fetcher = fetcher
        self.sources_cfg = sources_cfg or {}
        self.settings = settings or {}
        self.db = db

    def discover_all(self, force_mock: bool = False) -> Dict[str, Any]:
        """Runs full discovery sweep across seed portals and returns discovered content items."""
        pages, failed = self.sweep_seed_sources(force_mock=force_mock or (self.fetcher is None))
        items = []
        for p in pages:
            items.append({
                "url": p.url,
                "title": p.url.split("/")[-1] or "Opportunity Source Announcement",
                "content": p.text,
                "tier": p.tier,
                "category": p.category
            })
        return {
            "total_discovered": len(items),
            "items": items,
            "failed_sources": failed
        }


    def discover_from_queries(
        self,
        today_pkt: str,
        cycle: str,
        force_mock: bool = False
    ) -> List[DiscoveryItem]:
        """Runs configured discovery search queries using Gemini Google Search grounding."""
        queries = self.settings.get("discovery_queries", [])
        discovered: List[DiscoveryItem] = []
        seen_urls = set()

        if not self.gemini_client:
            logger.info("DiscoveryAgent: No Gemini client configured. Skipping query discovery.")
            return []

        for q in queries:
            query_str = q.get("query", "")
            focus = q.get("focus", "")
            category = "internships" if "internship" in query_str.lower() else "scholarships"
            try:
                items = self.gemini_client.run_discovery_query(
                    query=query_str,
                    focus=focus,
                    today_pkt=today_pkt,
                    cycle=cycle,
                    force_mock=force_mock
                )
                for item in items:
                    item.category = category
                    url_key = (item.official_url or item.other_url).lower().strip()
                    if url_key and url_key not in seen_urls:
                        seen_urls.add(url_key)
                        discovered.append(item)
            except Exception as e:
                logger.warning(f"Discovery query '{query_str}' failed: {e}")

        logger.info(f"DiscoveryAgent: Discovered {len(discovered)} candidate items via search queries.")
        return discovered

    def sweep_seed_sources(self, force_mock: bool = False) -> Tuple[List[PageContent], List[str]]:
        """Crawls configured seed sources (Tier 1 & 2 portals) to fetch raw page text and sublinks."""
        from typing import Tuple
        seed_sources = self.sources_cfg.get("sources", [])
        if not self.fetcher or force_mock:
            # Mock seed pages for offline test runs
            mock_pages = [
                PageContent("https://bkuc.edu.pk/financial-aid", "Bacha Khan University Charsadda Financial Aid and Merit Scholarships for KP students.", {}, tier=1, category="university"),
                PageContent("https://www.uop.edu.pk/sfao/", "University of Peshawar SFAO Notice: Need-based fee concessions and student scholarships.", {}, tier=1, category="university"),
                PageContent("https://uetpeshawar.edu.pk/financial-aid/", "UET Peshawar Directorate of Financial Aid: Engineering scholarships and internships.", {}, tier=1, category="university"),
                PageContent("https://www.hec.gov.pk/english/scholarshipsgrants/NBS/", "HEC Need Based Scholarships for undergraduate students enrolled in public sector universities.", {}, tier=1, category="federal_govt"),
                PageContent("https://ef.kp.gov.pk/scholarships", "KPEF Khyber Pakhtunkhwa Education Foundation scholarships for KP students.", {}, tier=1, category="provincial_govt"),
                PageContent("https://www.pseb.org.pk/internships", "Pakistan Software Export Board (PSEB) National IT Internship Program. Monthly stipend PKR 30,000 for BS Computer Science final year and fresh graduates.", {}, tier=1, category="internships"),
                PageContent("https://cern.ch/jobs/summer-student-programme", "CERN Summer Student Internship Programme for physics and engineering students worldwide including Pakistan.", {}, tier=1, category="international_internships")
            ]
            return mock_pages, []

        fetched_pages: List[PageContent] = []
        failed_sources: List[str] = []

        for src in seed_sources:
            url = src.get("url", "")
            tier = src.get("tier", 1)
            cat = src.get("category", "")
            page = self.fetcher.fetch_page(url, tier, cat)
            if page:
                fetched_pages.append(page)
                # Follow relevant sub-links
                sublinks = self.fetcher.find_relevant_sublinks(page)
                for sub_url in sublinks[:self.fetcher.follow_links_per_seed]:
                    sub_page = self.fetcher.fetch_page(sub_url, tier, cat)
                    if sub_page:
                        fetched_pages.append(sub_page)
            else:
                failed_sources.append(url)

        return fetched_pages, failed_sources
