"""Scraper for BDNS (Base de Datos Nacional de Subvenciones) via infosubvenciones.es.

This is the single most valuable structured source for NoraCenter.
The BDNS aggregates ALL public subsidies from ALL levels of government
in Spain (state, autonomous communities, local), and provides a REST API
returning JSON.
"""

import logging
from datetime import datetime

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)

# Base URL for the BDNS transparency portal
BDNS_BASE = "https://www.infosubvenciones.es/bdnstrans/GE/es"

# Culture-related search queries to run against the BDNS
CULTURE_QUERIES = [
    "cultura",
    "artes",
    "artistas",
    "creacion artistica",
    "musica",
    "teatro",
    "danza",
    "cine audiovisual",
    "literatura",
    "fotografia",
    "residencias artisticas",
    "patrimonio cultural",
    "museo",
    "artes escenicas",
    "artes visuales",
    "diseno",
]

# Map BDNS regions to our region format
CCAA_MAP = {
    "ANDALUCIA": "Andalucía",
    "ARAGON": "Aragón",
    "ASTURIAS": "Asturias",
    "ILLES BALEARS": "Islas Baleares",
    "CANARIAS": "Canarias",
    "CANTABRIA": "Cantabria",
    "CASTILLA Y LEON": "Castilla y León",
    "CASTILLA-LA MANCHA": "Castilla-La Mancha",
    "CATALUÑA": "Cataluña",
    "COMUNITAT VALENCIANA": "Comunidad Valenciana",
    "EXTREMADURA": "Extremadura",
    "GALICIA": "Galicia",
    "COMUNIDAD DE MADRID": "Madrid",
    "REGION DE MURCIA": "Murcia",
    "COMUNIDAD FORAL DE NAVARRA": "Navarra",
    "PAIS VASCO": "País Vasco",
    "LA RIOJA": "La Rioja",
    "CIUDAD DE CEUTA": "Ceuta",
    "CIUDAD DE MELILLA": "Melilla",
}


class BDNSScraper(BaseScraper):
    """Scraper for the Base de Datos Nacional de Subvenciones (BDNS).

    Uses the BDNS transparency portal search to find culture-related
    grants and subsidies across all levels of Spanish government.
    """

    name = "bdns"
    base_url = BDNS_BASE

    async def _search_bdns(self, query: str) -> list[RawOpportunity]:
        """Search BDNS for a specific query and parse results."""
        results = []

        # The BDNS portal allows searches via URL parameters
        search_url = (
            f"{BDNS_BASE}/convocatorias?"
            f"text={query.replace(' ', '+')}&"
            f"_csrf=&"
            f"situacion=Abierta"  # Only open calls
        )

        html = await self.fetch(search_url)
        if not html:
            return results

        soup = self.parse_html(html)

        # Find the results table/list
        rows = soup.find_all("tr", class_="filaTabla") or []

        # Also try div-based results (the site uses different layouts)
        if not rows:
            rows = soup.find_all("div", class_="resultado") or []

        if not rows:
            # Fallback: look for any structured listing
            table = soup.find("table", class_="tablaResultados")
            if table:
                rows = table.find_all("tr")[1:]  # Skip header

        for row in rows:
            try:
                # Try to extract data from table row
                cells = row.find_all("td")
                if cells and len(cells) >= 3:
                    title = cells[0].get_text(strip=True)
                    org = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    date_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                else:
                    # Try div-based layout
                    title_el = row.find(["h3", "h4", "a", "strong"])
                    title = title_el.get_text(strip=True) if title_el else ""
                    org = ""
                    date_text = ""

                if not title or len(title) < 5:
                    continue

                # Extract link
                link = row.find("a", href=True)
                if link:
                    href = link["href"]
                    if href.startswith("/"):
                        url = f"https://www.infosubvenciones.es{href}"
                    elif not href.startswith("http"):
                        url = f"{BDNS_BASE}/{href}"
                    else:
                        url = href
                else:
                    url = search_url

                # Try to parse deadline
                deadline = self._parse_date(date_text) if date_text else None

                # Try to identify region
                region = ""
                full_text = row.get_text()
                for key, value in CCAA_MAP.items():
                    if key.lower() in full_text.lower():
                        region = value
                        break
                if not region and "estado" in full_text.lower():
                    region = "Nacional"

                # Extract description
                desc_el = row.find("p") or row.find("div", class_="descripcion")
                description = desc_el.get_text(strip=True) if desc_el else title

                results.append(RawOpportunity(
                    title=title,
                    source_url=url,
                    source_name="BDNS - Infosubvenciones",
                    category="subvencion",
                    discipline="multidisciplinar",
                    organization=org or "Administración Pública",
                    region=region,
                    description=description[:500],
                    deadline=deadline,
                ))

            except Exception as e:
                logger.debug(f"Error parsing BDNS row: {e}")
                continue

        return results

    def _parse_date(self, text: str) -> datetime | None:
        """Parse date from BDNS format (dd/mm/yyyy)."""
        import re
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
        if m:
            try:
                return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                return None
        return None

    async def scrape(self) -> list[RawOpportunity]:
        """Search BDNS with all culture-related queries."""
        results = []
        seen_urls = set()

        for query in CULTURE_QUERIES:
            try:
                query_results = await self._search_bdns(query)
                for opp in query_results:
                    if opp.source_url not in seen_urls:
                        seen_urls.add(opp.source_url)
                        results.append(opp)
            except Exception as e:
                logger.error(f"BDNS search failed for '{query}': {e}")

        logger.info(f"BDNS: Found {len(results)} unique opportunities")
        return results
