"""Scrapers for Comunidades Autónomas cultural departments.

Each comunidad has its own website with cultural grants and opportunities.
This scraper covers the main ones.
"""

import logging
import re
from datetime import datetime

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)


COMUNIDADES = [
    {
        "name": "Comunidad de Madrid - Cultura",
        "url": "https://www.comunidad.madrid/servicios/cultura/ayudas-subvenciones-cultura",
        "region": "Madrid",
        "org": "Comunidad de Madrid",
    },
    {
        "name": "Generalitat de Catalunya - Cultura",
        "url": "https://cultura.gencat.cat/ca/departament/beques-premis-i-subvencions/subvencions/",
        "region": "Cataluña",
        "org": "Generalitat de Catalunya",
    },
    {
        "name": "Junta de Andalucía - Cultura",
        "url": "https://www.juntadeandalucia.es/cultura/ayudas",
        "region": "Andalucía",
        "org": "Junta de Andalucía",
    },
    {
        "name": "Generalitat Valenciana - Cultura",
        "url": "https://ceice.gva.es/es/web/cultura/subvenciones",
        "region": "Comunidad Valenciana",
        "org": "Generalitat Valenciana",
    },
    {
        "name": "Gobierno Vasco - Cultura",
        "url": "https://www.euskadi.eus/gobierno-vasco/ayudas-cultura/",
        "region": "País Vasco",
        "org": "Gobierno Vasco",
    },
    {
        "name": "Xunta de Galicia - Cultura",
        "url": "https://www.cultura.gal/es/axudas",
        "region": "Galicia",
        "org": "Xunta de Galicia",
    },
]


class ComunidadesScraper(BaseScraper):
    """Scrapes cultural opportunities from autonomous community websites."""

    name = "comunidades"

    def _extract_deadline(self, text: str) -> datetime | None:
        months = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
            "gener": 1, "febrer": 2, "març": 3, "maig": 5,
            "juny": 6, "juliol": 7, "agost": 8, "setembre": 9,
            "novembre": 11, "desembre": 12,  # Catalan months
        }
        m = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", text)
        if m:
            day, month_name, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
            if month_name in months:
                return datetime(year, months[month_name], day)

        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
        if m:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))

        return None

    async def _scrape_comunidad(self, comunidad: dict) -> list[RawOpportunity]:
        results = []
        html = await self.fetch(comunidad["url"])
        if not html:
            return results

        soup = self.parse_html(html)
        main = soup.find("main") or soup.find("div", id="content") or soup

        links = main.find_all("a", href=True)
        for link in links:
            title = link.get_text(strip=True)
            href = link["href"]

            if not title or len(title) < 10:
                continue
            if any(skip in href for skip in ["#", "javascript:", "mailto:"]):
                continue

            # Make URL absolute
            if href.startswith("/"):
                base = comunidad["url"].split("/")[0:3]
                url = "/".join(base) + href
            elif not href.startswith("http"):
                url = comunidad["url"].rstrip("/") + "/" + href
            else:
                url = href

            parent = link.find_parent(["li", "div", "article", "tr", "p"])
            parent_text = parent.get_text() if parent else ""
            deadline = self._extract_deadline(parent_text)

            results.append(RawOpportunity(
                title=title,
                source_url=url,
                source_name=comunidad["name"],
                category="subvencion",
                discipline="multidisciplinar",
                organization=comunidad["org"],
                region=comunidad["region"],
                description=parent_text[:500] if parent_text else "",
                deadline=deadline,
            ))

        return results

    async def scrape(self) -> list[RawOpportunity]:
        results = []
        for comunidad in COMUNIDADES:
            try:
                found = await self._scrape_comunidad(comunidad)
                results.extend(found)
            except Exception as e:
                logger.error(f"Error scraping {comunidad['name']}: {e}")
        return results
