"""Scraper for WordPress-based art/culture sites.

Many Spanish art platforms run on WordPress and expose standard RSS feeds
at /feed/ or /category/convocatorias/feed/. This scraper leverages that.
"""

import logging
from datetime import datetime

import feedparser

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)


class WordPressSite:
    """Configuration for a WordPress-based art site."""

    def __init__(self, name: str, feed_url: str, category: str = "convocatoria",
                 discipline: str = "multidisciplinar", region: str = "Nacional"):
        self.name = name
        self.feed_url = feed_url
        self.category = category
        self.discipline = discipline
        self.region = region


# WordPress-based Spanish art sites with known RSS feeds
WP_SITES = [
    WordPressSite(
        name="Exibart.es - Convocatorias",
        feed_url="https://www.exibart.es/categoria/convocatorias/feed/",
        category="convocatoria",
        discipline="artes_visuales",
    ),
    WordPressSite(
        name="masdearte.com - Convocatorias",
        feed_url="https://masdearte.com/convocatorias/feed/",
        category="convocatoria",
        discipline="artes_visuales",
    ),
    WordPressSite(
        name="PAC - Convocatorias",
        feed_url="https://www.plataformadeartecontemporaneo.com/pac/category/convocatorias/feed/",
        category="convocatoria",
        discipline="artes_visuales",
    ),
    WordPressSite(
        name="Hipermedula - Convocatorias",
        feed_url="https://hipermedula.org/convocatorias/feed/",
        category="convocatoria",
        discipline="artes_digitales",
    ),
    WordPressSite(
        name="Recursos Culturales",
        feed_url="https://www.recursosculturales.com/feed/",
        category="convocatoria",
        discipline="multidisciplinar",
    ),
]


class WordPressScraper(BaseScraper):
    """Scrapes opportunities from WordPress-based art sites via RSS."""

    name = "wordpress_sites"

    def _parse_date(self, entry) -> datetime | None:
        for attr in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime(*parsed[:6])
                except (TypeError, ValueError):
                    continue
        return None

    async def _scrape_site(self, site: WordPressSite) -> list[RawOpportunity]:
        results = []

        content = await self.fetch(site.feed_url)
        if not content:
            return results

        feed = feedparser.parse(content)

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))

            if not title or not link:
                continue

            # Strip HTML tags from summary
            from bs4 import BeautifulSoup
            if summary:
                summary = BeautifulSoup(summary, "lxml").get_text(strip=True)

            results.append(RawOpportunity(
                title=title,
                source_url=link,
                source_name=site.name,
                category=site.category,
                discipline=site.discipline,
                region=site.region,
                description=summary[:500] if summary else "",
                publication_date=self._parse_date(entry),
            ))

        return results

    async def scrape(self) -> list[RawOpportunity]:
        results = []

        for site in WP_SITES:
            try:
                site_results = await self._scrape_site(site)
                results.extend(site_results)
                logger.info(f"WordPress [{site.name}]: {len(site_results)} entries")
            except Exception as e:
                logger.error(f"Error scraping {site.name}: {e}")

        return results
