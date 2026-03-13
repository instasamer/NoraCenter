"""Scraper for BOE (Boletín Oficial del Estado).

Searches for culture-related grants, scholarships, and public positions
in the official gazette.
"""

import logging
import re
from datetime import datetime

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)

# BOE search API for cultural topics
SEARCH_QUERIES = [
    "becas+cultura+artistas",
    "subvenciones+cultura+artes",
    "ayudas+creacion+artistica",
    "residencias+artisticas",
    "premios+cultura+arte",
]


class BOEScraper(BaseScraper):
    """Scraper for the Boletín Oficial del Estado (boe.es)."""

    name = "boe"
    base_url = "https://www.boe.es"

    def _parse_boe_date(self, text: str) -> datetime | None:
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
        if m:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        return None

    async def _search_boe(self, query: str) -> list[RawOpportunity]:
        """Search BOE using their search page."""
        results = []
        url = (
            f"{self.base_url}/buscar/doc.php?"
            f"campo%5B0%5D=ORI&dato%5B0%5D=3&"  # Section III (authority dispositions)
            f"texto_libre={query}&"
            f"operador%5B1%5D=and&"
            f"page_hits=20&orden=fecha"
        )

        html = await self.fetch(url)
        if not html:
            return results

        soup = self.parse_html(html)
        items = soup.find_all("li", class_="dispo")

        for item in items:
            link = item.find("a", href=True)
            if not link:
                continue

            title = link.get_text(strip=True)
            href = link["href"]

            if not title:
                continue

            full_url = f"{self.base_url}{href}" if href.startswith("/") else href

            # Extract date from the item
            date_el = item.find("span", class_="fecha")
            pub_date = None
            if date_el:
                pub_date = self._parse_boe_date(date_el.get_text())

            # Extract department/organization
            dept_el = item.find("span", class_="departamento")
            org = dept_el.get_text(strip=True) if dept_el else ""

            description = item.get_text(strip=True)[:500]

            results.append(RawOpportunity(
                title=title,
                source_url=full_url,
                source_name="BOE",
                category="subvencion",
                discipline="multidisciplinar",
                organization=org or "BOE",
                region="Nacional",
                description=description,
                publication_date=pub_date,
            ))

        return results

    async def scrape(self) -> list[RawOpportunity]:
        results = []
        for query in SEARCH_QUERIES:
            query_results = await self._search_boe(query)
            results.extend(query_results)

        # Deduplicate by URL
        seen = set()
        unique = []
        for opp in results:
            if opp.source_url not in seen:
                seen.add(opp.source_url)
                unique.append(opp)

        return unique
