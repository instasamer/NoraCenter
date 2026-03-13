"""Generic RSS/Atom feed scraper for sources that provide feeds."""

import logging
from datetime import datetime

import feedparser

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)


class RSSSource:
    """Configuration for a single RSS source."""

    def __init__(
        self,
        name: str,
        feed_url: str,
        category: str = "",
        discipline: str = "",
        region: str = "",
        organization: str = "",
    ):
        self.name = name
        self.feed_url = feed_url
        self.category = category
        self.discipline = discipline
        self.region = region
        self.organization = organization


class RSSScraper(BaseScraper):
    """Scrapes opportunities from RSS/Atom feeds."""

    name = "rss_feeds"

    SOURCES = [
        # BOE - Sección de ayudas y subvenciones (cultura)
        RSSSource(
            name="BOE - Ayudas",
            feed_url="https://www.boe.es/rss/canal.php?c=ayudas",
            category="subvencion",
            region="Nacional",
            organization="Boletín Oficial del Estado",
        ),
        # Ministerio de Cultura - Noticias / Ayudas
        RSSSource(
            name="Ministerio de Cultura",
            feed_url="https://www.cultura.gob.es/rss/cultura.xml",
            category="convocatoria",
            region="Nacional",
            organization="Ministerio de Cultura",
        ),
        # INAEM (Artes escénicas y música)
        RSSSource(
            name="INAEM",
            feed_url="https://www.cultura.gob.es/rss/inaem.xml",
            category="convocatoria",
            discipline="multidisciplinar",
            region="Nacional",
            organization="INAEM",
        ),
        # Acción Cultural Española (AC/E)
        RSSSource(
            name="AC/E",
            feed_url="https://www.accioncultural.es/es/rss",
            category="convocatoria",
            region="Nacional",
            organization="Acción Cultural Española",
        ),
    ]

    def _parse_date(self, entry) -> datetime | None:
        """Parse date from a feed entry."""
        for attr in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime(*parsed[:6])
                except (TypeError, ValueError):
                    continue
        return None

    def _is_culture_related(self, text: str) -> bool:
        """Check if text is related to culture/arts."""
        keywords = [
            "cultur", "artist", "arte", "música", "teatro", "danza",
            "cine", "literatur", "fotograf", "diseño", "creativ",
            "beca", "residencia", "exposici", "festival", "escénic",
            "patrimonio", "museo", "galería", "audiovisual",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    async def scrape(self) -> list[RawOpportunity]:
        results = []

        for source in self.SOURCES:
            try:
                content = await self.fetch(source.feed_url)
                if not content:
                    continue

                feed = feedparser.parse(content)

                for entry in feed.entries:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    link = entry.get("link", "")

                    combined_text = f"{title} {summary}"
                    if not self._is_culture_related(combined_text):
                        continue

                    opp = RawOpportunity(
                        title=title,
                        description=summary,
                        source_url=link,
                        source_name=source.name,
                        category=source.category,
                        discipline=source.discipline,
                        organization=source.organization,
                        region=source.region,
                        publication_date=self._parse_date(entry),
                    )
                    results.append(opp)

            except Exception as e:
                logger.error(f"Error processing RSS source {source.name}: {e}")
                continue

        return results
