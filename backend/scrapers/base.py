"""Base scraper with common functionality for all source scrapers."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class RawOpportunity:
    """Intermediate representation of a scraped opportunity."""

    title: str
    source_url: str
    source_name: str
    description: str = ""
    category: str = ""
    discipline: str = ""
    organization: str = ""
    location: str = ""
    region: str = ""
    deadline: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    publication_date: datetime | None = None
    funding_amount: str = ""
    extra: dict = field(default_factory=dict)


class BaseScraper(ABC):
    """Base class for all scrapers."""

    name: str = "base"
    base_url: str = ""
    rate_limit_seconds: float = 2.0

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; NoraCenter/1.0; "
                    "+https://noracenter.es; cultural aggregator)"
                ),
                "Accept-Language": "es-ES,es;q=0.9",
            },
        )

    async def close(self):
        await self.client.aclose()

    async def fetch(self, url: str) -> str:
        """Fetch a URL and return its text content."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"[{self.name}] Error fetching {url}: {e}")
            return ""

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    async def scrape(self) -> list[RawOpportunity]:
        """Scrape opportunities from this source. Must be implemented."""
        ...

    async def run(self) -> list[RawOpportunity]:
        """Execute the scraper with error handling."""
        logger.info(f"[{self.name}] Starting scrape...")
        try:
            results = await self.scrape()
            logger.info(f"[{self.name}] Found {len(results)} opportunities")
            return results
        except Exception as e:
            logger.error(f"[{self.name}] Scrape failed: {e}", exc_info=True)
            return []
        finally:
            await self.close()
