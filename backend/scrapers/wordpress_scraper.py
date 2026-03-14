"""Scraper for WordPress-based art/culture sites via RSS feeds."""

import logging

from bs4 import BeautifulSoup

from backend.scrapers.base import BaseScraper, RawOpportunity
from backend.scrapers.feed_parser import parse_feed

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

    async def _scrape_site(self, site: WordPressSite) -> list[RawOpportunity]:
        results = []

        content = await self.fetch(site.feed_url)
        if not content:
            return results

        entries = parse_feed(content)

        for entry in entries:
            if not entry.title or not entry.link:
                continue

            # Strip HTML tags from summary
            summary = entry.summary
            if summary and "<" in summary:
                summary = BeautifulSoup(summary, "lxml").get_text(strip=True)

            results.append(RawOpportunity(
                title=entry.title,
                source_url=entry.link,
                source_name=site.name,
                category=site.category,
                discipline=site.discipline,
                region=site.region,
                description=summary[:500] if summary else "",
                publication_date=entry.published,
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
