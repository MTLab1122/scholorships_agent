"""Web and PDF fetcher module.
Fetches static HTML via requests + BeautifulSoup, PDFs via pypdf,
extracts text and link maps, and follows relevant scholarship sub-links.
"""

import io
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

logger = logging.getLogger(__name__)

RELEVANT_ANCHOR_PATTERNS = [
    r"scholarship",
    r"financial\s+aid",
    r"fee\s+waiver",
    r"stipend",
    r"grant",
    r"interest[- ]free\s+loan",
    r"qarz[- ]e[- ]hasna",
    r"apply",
    r"advertisement",
    r"notice",
    r"sfao",
    r"welfare",
    r"endowment",
    r"ehsaas",
    r"hec"
]

ANCHOR_REGEX = re.compile("|".join(RELEVANT_ANCHOR_PATTERNS), re.IGNORECASE)


class PageContent:
    def __init__(self, url: str, text: str, links: Dict[str, str], tier: int, category: str = "", is_pdf: bool = False):
        self.url = url
        self.text = text
        self.links = links
        self.tier = tier
        self.category = category
        self.is_pdf = is_pdf


class ContentFetcher:
    def __init__(
        self,
        user_agent: str,
        timeout: int = 25,
        follow_links_per_seed: int = 5
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.follow_links_per_seed = follow_links_per_seed
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
            "Connection": "keep-alive",
        })

    def fetch_url(self, url: str, tier: int = 1, category: str = "") -> Optional[PageContent]:
        """Fetches a URL (HTML or PDF) and extracts text and hyperlinks."""
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code >= 400:
                logger.warning(f"HTTP {resp.status_code} when fetching {url}")
                return None

            content_type = resp.headers.get("Content-Type", "").lower()
            final_url = resp.url

            # PDF Handling
            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                return self._parse_pdf(resp.content, final_url, tier, category)

            # HTML Handling
            return self._parse_html(resp.text, final_url, tier, category)

        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None

    def _parse_pdf(self, content_bytes: bytes, url: str, tier: int, category: str) -> Optional[PageContent]:
        try:
            reader = PdfReader(io.BytesIO(content_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts).strip()
            if not full_text:
                full_text = "PDF document with no extractable text."
            
            return PageContent(
                url=url,
                text=full_text,
                links={url: url},
                tier=tier,
                category=category,
                is_pdf=True
            )
        except Exception as e:
            logger.warning(f"Failed to parse PDF from {url}: {e}")
            return None

    def _parse_html(self, html_text: str, url: str, tier: int, category: str) -> PageContent:
        soup = BeautifulSoup(html_text, "html.parser")

        # Remove script, style, nav, footer tags that clutter text
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        # Extract links: anchor text -> absolute url
        links_map: Dict[str, str] = {}
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            abs_url = urljoin(url, href)
            anchor_text = " ".join(a.get_text().split()).strip()
            if abs_url.startswith("http"):
                links_map[anchor_text or abs_url] = abs_url

        # Extract clean body text
        text = soup.get_text(separator="\n")
        # Collapse excessive newlines/spaces
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        return PageContent(
            url=url,
            text=clean_text[:60000], # Keep within reasonable context window
            links=links_map,
            tier=tier,
            category=category,
            is_pdf=False
        )

    def extract_sublinks(self, page_content: PageContent) -> List[str]:
        """Finds up to follow_links_per_seed sub-links matching scholarship keywords."""
        if page_content.is_pdf:
            return []

        base_domain = urlparse(page_content.url).netloc
        discovered_urls: List[str] = []

        for anchor_text, target_url in page_content.links.items():
            if len(discovered_urls) >= self.follow_links_per_seed:
                break

            target_domain = urlparse(target_url).netloc
            # Stay on the same or related official domain
            if base_domain in target_domain or target_domain in base_domain or "gov.pk" in target_domain or "edu.pk" in target_domain:
                if ANCHOR_REGEX.search(anchor_text) or ANCHOR_REGEX.search(target_url):
                    if target_url not in discovered_urls and target_url != page_content.url:
                        discovered_urls.append(target_url)

        return discovered_urls
