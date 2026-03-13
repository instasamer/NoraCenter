"""Scraper for cultura.gob.es - Ministerio de Cultura y Deporte de España.

Scrapes becas, ayudas y subvenciones from the official ministry pages.
"""

import logging
import re
from datetime import datetime

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)

# Main sections to scrape
SECTIONS = [
    {
        "url": "https://www.cultura.gob.es/servicios-al-ciudadano/catalogo/becas-ayudas-y-subvenciones.html",
        "category": "subvencion",
        "label": "Becas, ayudas y subvenciones",
    },
    {
        "url": "https://www.cultura.gob.es/cultura/artesplasticas/convocatorias.html",
        "category": "convocatoria",
        "label": "Artes plásticas - Convocatorias",
    },
    {
        "url": "https://www.cultura.gob.es/cultura/libro/convocatorias.html",
        "category": "convocatoria",
        "label": "Libro y lectura - Convocatorias",
    },
]


class CulturaGobScraper(BaseScraper):
    """Scraper for Ministerio de Cultura (cultura.gob.es)."""

    name = "cultura_gob"
    base_url = "https://www.cultura.gob.es"

    def _make_absolute(self, url: str) -> str:
        if url.startswith("http"):
            return url
        if url.startswith("/"):
            return f"{self.base_url}{url}"
        return f"{self.base_url}/{url}"

    def _parse_spanish_date(self, text: str) -> datetime | None:
        """Try to parse common Spanish date formats."""
        months = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
        }
        # Pattern: "31 de enero de 2026" or "31/01/2026"
        m = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", text)
        if m:
            day, month_name, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
            if month_name in months:
                return datetime(year, months[month_name], day)

        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
        if m:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))

        return None

    async def _scrape_section(self, section: dict) -> list[RawOpportunity]:
        results = []
        html = await self.fetch(section["url"])
        if not html:
            return results

        soup = self.parse_html(html)

        # Look for links in content areas - the ministry site uses various layouts
        content = soup.find("div", class_="contenido") or soup.find("main") or soup
        links = content.find_all("a", href=True)

        for link in links:
            title = link.get_text(strip=True)
            href = link["href"]

            if not title or len(title) < 10:
                continue

            # Skip navigation/menu links
            if any(skip in href for skip in ["#", "javascript:", "mailto:", ".pdf"]):
                continue

            url = self._make_absolute(href)

            # Look for deadline in surrounding text
            parent = link.find_parent(["li", "div", "tr", "p"])
            parent_text = parent.get_text() if parent else ""
            deadline = self._parse_spanish_date(parent_text)

            results.append(RawOpportunity(
                title=title,
                source_url=url,
                source_name=f"Ministerio de Cultura - {section['label']}",
                category=section["category"],
                discipline="multidisciplinar",
                organization="Ministerio de Cultura y Deporte",
                region="Nacional",
                description=parent_text[:500] if parent_text else "",
                deadline=deadline,
            ))

        return results

    async def scrape(self) -> list[RawOpportunity]:
        results = []
        for section in SECTIONS:
            section_results = await self._scrape_section(section)
            results.extend(section_results)
        return results
