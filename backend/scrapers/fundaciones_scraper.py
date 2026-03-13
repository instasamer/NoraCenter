"""Scrapers for major Spanish private foundations that offer artist opportunities."""

import logging
import re
from datetime import datetime

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)


class FundacionesScraper(BaseScraper):
    """Scrapes opportunities from major Spanish private foundations."""

    name = "fundaciones"

    FOUNDATIONS = [
        {
            "name": "Fundación BBVA",
            "url": "https://www.fbbva.es/convocatorias/",
            "org": "Fundación BBVA",
            "selector": {"tag": "article", "class": "convocatoria"},
        },
        {
            "name": "Fundación La Caixa",
            "url": "https://fundacionlacaixa.org/es/becas-y-ayudas",
            "org": "Fundación La Caixa",
            "selector": {"tag": "div", "class": "card"},
        },
        {
            "name": "Fundación Botín",
            "url": "https://www.fundacionbotin.org/programas/arte-y-cultura/becas-y-talleres.html",
            "org": "Fundación Botín",
            "selector": {"tag": "div", "class": "item"},
        },
        {
            "name": "Casa de Velázquez",
            "url": "https://www.casadevelazquez.org/es/convocatorias/",
            "org": "Casa de Velázquez",
            "selector": {"tag": "article"},
        },
        {
            "name": "Matadero Madrid",
            "url": "https://www.mataderomadrid.org/programas/convocatorias",
            "org": "Matadero Madrid",
            "selector": {"tag": "div", "class": "view-content"},
        },
    ]

    ART_KEYWORDS = [
        "arte", "artist", "cultur", "creaci", "beca", "residencia",
        "exposici", "music", "teatro", "danza", "fotograf", "cine",
        "diseño", "literatur", "escénic", "visual",
    ]

    def _is_art_related(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.ART_KEYWORDS)

    def _extract_deadline(self, text: str) -> datetime | None:
        months = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
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

    async def _scrape_foundation(self, foundation: dict) -> list[RawOpportunity]:
        results = []
        html = await self.fetch(foundation["url"])
        if not html:
            return results

        soup = self.parse_html(html)
        sel = foundation["selector"]
        containers = soup.find_all(
            sel["tag"],
            class_=sel.get("class"),
        )

        # If specific selectors don't find anything, fall back to links in main content
        if not containers:
            main = soup.find("main") or soup.find("div", id="content") or soup
            containers = [main]

        for container in containers:
            links = container.find_all("a", href=True)
            for link in links:
                title = link.get_text(strip=True)
                href = link["href"]

                if not title or len(title) < 10:
                    continue
                if any(skip in href for skip in ["#", "javascript:", "mailto:"]):
                    continue

                # Make URL absolute
                if href.startswith("/"):
                    base = foundation["url"].split("/")[0:3]
                    url = "/".join(base) + href
                elif not href.startswith("http"):
                    url = foundation["url"].rstrip("/") + "/" + href
                else:
                    url = href

                parent = link.find_parent(["li", "div", "article", "tr", "p"])
                parent_text = parent.get_text() if parent else title
                deadline = self._extract_deadline(parent_text)

                results.append(RawOpportunity(
                    title=title,
                    source_url=url,
                    source_name=foundation["name"],
                    category="beca",
                    discipline="multidisciplinar",
                    organization=foundation["org"],
                    region="Nacional",
                    description=parent_text[:500],
                    deadline=deadline,
                ))

        return results

    async def scrape(self) -> list[RawOpportunity]:
        results = []
        for foundation in self.FOUNDATIONS:
            try:
                found = await self._scrape_foundation(foundation)
                results.extend(found)
            except Exception as e:
                logger.error(f"Error scraping {foundation['name']}: {e}")
        return results
