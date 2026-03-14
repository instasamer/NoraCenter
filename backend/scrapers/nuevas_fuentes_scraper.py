"""
Nuevas fuentes de oportunidades para artistas en España y Europa.

Fuentes cubiertas:
- Injuve (Instituto de la Juventud)
- Teatros del Canal (Madrid)
- Conde Duque Madrid
- Fundación SGAE
- La Caldera (Barcelona, danza)
- Fundación Daniel y Nina Carasso
- Red Española de Teatros, Circo y Danza (RETECID)
- Centro Dramático Nacional
- Naves Matadero (escénicas)
- Creative Europe (convocatorias europeas)
- Artfacts / convocatorias internacionales
- Tabacalera (Madrid)
- Centro Coreográfico de Galicia
- L'animal a l'esquena (Girona, danza)
- Arts Council (referencia europea)
"""

import logging
import re
from datetime import datetime

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)


class NuevasFuentesScraper(BaseScraper):
    """Scrapes nuevas fuentes de oportunidades para artistas."""

    name = "nuevas_fuentes"

    SOURCES = [
        # --- Instituciones públicas ---
        {
            "name": "Injuve - Becas y Residencias",
            "url": "https://www.injuve.es/convocatorias/becas",
            "org": "Instituto de la Juventud (Injuve)",
            "category": "beca",
            "discipline": "multidisciplinar",
            "region": "Nacional",
        },
        {
            "name": "Centro Dramático Nacional",
            "url": "https://cdn.mcu.es/category/convocatorias/",
            "org": "Centro Dramático Nacional",
            "category": "convocatoria",
            "discipline": "teatro",
            "region": "Nacional",
        },
        {
            "name": "Teatros del Canal - Residencias",
            "url": "https://www.teatroscanal.com/centro-danza-madrid/convocatoria/",
            "org": "Teatros del Canal",
            "category": "residencia",
            "discipline": "danza",
            "region": "Madrid",
        },
        {
            "name": "Conde Duque Madrid - Convocatorias",
            "url": "https://www.condeduquemadrid.es/convocatorias",
            "org": "Conde Duque Madrid",
            "category": "residencia",
            "discipline": "artes escénicas",
            "region": "Madrid",
        },
        {
            "name": "Tabacalera - Convocatorias",
            "url": "https://www.tabacalera.es/convocatorias/",
            "org": "Tabacalera / Ministerio de Cultura",
            "category": "residencia",
            "discipline": "artes visuales",
            "region": "Madrid",
        },
        {
            "name": "INAEM - Convocatorias",
            "url": "https://www.inaem.gob.es/convocatorias-ayudas-y-subvenciones",
            "org": "INAEM",
            "category": "subvención",
            "discipline": "artes escénicas",
            "region": "Nacional",
        },
        # --- Fundaciones privadas ---
        {
            "name": "Fundación SGAE - Becas",
            "url": "https://www.fundacion-sgae.es/es/becas-y-ayudas",
            "org": "Fundación SGAE",
            "category": "beca",
            "discipline": "música",
            "region": "Nacional",
        },
        {
            "name": "Fundación Daniel y Nina Carasso",
            "url": "https://www.fundacioncarasso.org/es/convocatorias/",
            "org": "Fundación Daniel y Nina Carasso",
            "category": "beca",
            "discipline": "multidisciplinar",
            "region": "Nacional",
        },
        {
            "name": "Fundación Banco Santander - Cultura",
            "url": "https://www.fundacionbancosantander.com/es/arte-y-cultura/convocatorias.html",
            "org": "Fundación Banco Santander",
            "category": "beca",
            "discipline": "multidisciplinar",
            "region": "Nacional",
        },
        {
            "name": "Fundación Telefónica - Convocatorias",
            "url": "https://espacio.fundaciontelefonica.com/convocatorias/",
            "org": "Fundación Telefónica",
            "category": "beca",
            "discipline": "multidisciplinar",
            "region": "Nacional",
        },
        # --- Espacios de danza y artes escénicas ---
        {
            "name": "La Caldera - Residencias",
            "url": "https://lacaldera.info/residencies/",
            "org": "La Caldera",
            "category": "residencia",
            "discipline": "danza",
            "region": "Cataluña",
        },
        {
            "name": "L'animal a l'esquena - Residencias",
            "url": "https://www.animalasquena.net/residencies",
            "org": "L'animal a l'esquena",
            "category": "residencia",
            "discipline": "danza",
            "region": "Cataluña",
        },
        {
            "name": "Centro Coreográfico de Galicia",
            "url": "https://www.centrocoreograficogalicia.org/convocatorias",
            "org": "Centro Coreográfico de Galicia",
            "category": "residencia",
            "discipline": "danza",
            "region": "Galicia",
        },
        # --- Plataformas y redes ---
        {
            "name": "Artisting - Convocatorias",
            "url": "https://artisting.es/convocatorias/",
            "org": "Artisting",
            "category": "convocatoria",
            "discipline": "multidisciplinar",
            "region": "Nacional",
        },
        {
            "name": "infoculture.info - Convocatorias",
            "url": "https://www.infoculture.info/secciones/convocatorias/",
            "org": "InfoCulture",
            "category": "convocatoria",
            "discipline": "multidisciplinar",
            "region": "Nacional",
        },
        # --- Europa ---
        {
            "name": "Creative Europe - Calls",
            "url": "https://culture.ec.europa.eu/calls",
            "org": "European Commission / Creative Europe",
            "category": "subvención",
            "discipline": "multidisciplinar",
            "region": "Europa",
        },
    ]

    ART_KEYWORDS = [
        "arte", "artist", "cultur", "creaci", "beca", "residencia",
        "exposici", "music", "teatro", "danza", "fotograf", "cine",
        "diseño", "literatur", "escénic", "visual", "convocatoria",
        "subvenci", "ayuda", "premio", "concurso", "taller", "festival",
    ]

    SKIP_PATTERNS = ["#", "javascript:", "mailto:", "tel:", "whatsapp:"]

    def _is_art_related(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.ART_KEYWORDS)

    def _extract_deadline(self, text: str) -> datetime | None:
        months = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        }
        m = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", text, re.IGNORECASE)
        if m:
            day, month_name, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
            if month_name in months:
                try:
                    return datetime(year, months[month_name], day)
                except ValueError:
                    pass

        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
        if m:
            try:
                return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass

        return None

    def _make_absolute_url(self, href: str, base_url: str) -> str:
        if href.startswith("http"):
            return href
        if href.startswith("//"):
            return "https:" + href
        if href.startswith("/"):
            parts = base_url.split("/")
            return f"{parts[0]}//{parts[2]}{href}"
        return base_url.rstrip("/") + "/" + href

    async def _scrape_source(self, source: dict) -> list[RawOpportunity]:
        results = []
        html = await self.fetch(source["url"])
        if not html:
            return results

        soup = self.parse_html(html)

        # Try to find main content area
        main = (
            soup.find("main")
            or soup.find("div", id="content")
            or soup.find("div", class_=re.compile(r"content|main|container", re.I))
            or soup
        )

        # Find all links in content area
        links = main.find_all("a", href=True)

        seen_urls = set()
        for link in links:
            title = link.get_text(strip=True)
            href = link["href"]

            if not title or len(title) < 8:
                continue
            if any(skip in href for skip in self.SKIP_PATTERNS):
                continue
            if not self._is_art_related(title):
                continue

            url = self._make_absolute_url(href, source["url"])

            if url in seen_urls or url == source["url"]:
                continue
            seen_urls.add(url)

            # Get surrounding context for description and deadline
            parent = link.find_parent(["li", "article", "div", "tr", "p", "section"])
            parent_text = parent.get_text(strip=True)[:600] if parent else title
            deadline = self._extract_deadline(parent_text)

            results.append(RawOpportunity(
                title=title,
                source_url=url,
                source_name=source["name"],
                category=source["category"],
                discipline=source["discipline"],
                organization=source["org"],
                region=source["region"],
                description=parent_text,
                deadline=deadline,
            ))

        logger.info(f"[{source['name']}] Found {len(results)} opportunities")
        return results

    async def scrape(self) -> list[RawOpportunity]:
        all_results = []
        for source in self.SOURCES:
            try:
                found = await self._scrape_source(source)
                all_results.extend(found)
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
        return all_results
