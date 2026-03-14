"""Generic RSS/Atom feed scraper for sources that provide feeds."""

import logging
from datetime import datetime

from backend.scrapers.base import BaseScraper, RawOpportunity
from backend.scrapers.feed_parser import parse_feed

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

                entries = parse_feed(content)

                for entry in entries:
                    combined_text = f"{entry.title} {entry.summary}"
                    if not self._is_culture_related(combined_text):
                        continue

                    opp = RawOpportunity(
                        title=entry.title,
                        description=entry.summary,
                        source_url=entry.link,
                        source_name=source.name,
                        category=source.category,
                        discipline=source.discipline,
                        organization=source.organization,
                        region=source.region,
                        publication_date=entry.published,
                    )
                    results.append(opp)

            except Exception as e:
                logger.error(f"Error processing RSS source {source.name}: {e}")
                continue

        return results
