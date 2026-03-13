"""Scraper using the BOE Open Data API.

The BOE provides a REST API (OpenAPI v3.1) at boe.es/datosabiertos/api/
that returns daily summaries in structured format. This is more reliable
than HTML scraping.

API endpoint: GET boe.es/datosabiertos/api/boe/sumario/YYYYMMDD
"""

import logging
import re
from datetime import datetime, timedelta

from backend.scrapers.base import BaseScraper, RawOpportunity

logger = logging.getLogger(__name__)

BOE_API_BASE = "https://www.boe.es/datosabiertos/api/boe/sumario"

# Culture-related keywords to filter BOE entries
CULTURE_KEYWORDS = [
    "cultur", "artist", "arte", "música", "teatro", "danza",
    "cine", "literatur", "fotograf", "diseño", "creativ",
    "beca", "residencia", "exposici", "festival", "escénic",
    "patrimonio", "museo", "galería", "audiovisual", "cinemat",
    "inaem", "libro", "lectura", "bibliotec",
]


class BOEAPIScraper(BaseScraper):
    """Scraper that uses the official BOE Open Data API."""

    name = "boe_api"
    base_url = "https://www.boe.es"

    def _is_culture_related(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in CULTURE_KEYWORDS)

    async def _fetch_summary(self, date: datetime) -> list[RawOpportunity]:
        """Fetch and parse the BOE summary for a given date."""
        results = []
        date_str = date.strftime("%Y%m%d")
        url = f"{BOE_API_BASE}/{date_str}"

        try:
            response = await self.client.get(
                url,
                headers={"Accept": "application/json"},
            )
            if response.status_code != 200:
                logger.debug(f"BOE API returned {response.status_code} for {date_str}")
                return results

            data = response.json()
        except Exception as e:
            logger.error(f"BOE API error for {date_str}: {e}")
            return results

        # Navigate the BOE API response structure
        # The structure is: data > sumario > diario > seccion > departamento > epigrafe > item
        try:
            sumario = data.get("data", {}).get("sumario", {})
            diarios = sumario.get("diario", [])
            if isinstance(diarios, dict):
                diarios = [diarios]

            for diario in diarios:
                secciones = diario.get("seccion", [])
                if isinstance(secciones, dict):
                    secciones = [secciones]

                for seccion in secciones:
                    departamentos = seccion.get("departamento", [])
                    if isinstance(departamentos, dict):
                        departamentos = [departamentos]

                    for dept in departamentos:
                        dept_name = dept.get("@nombre", "")
                        epigrafes = dept.get("epigrafe", [])
                        if isinstance(epigrafes, dict):
                            epigrafes = [epigrafes]

                        for epigrafe in epigrafes:
                            items = epigrafe.get("item", [])
                            if isinstance(items, dict):
                                items = [items]

                            for item in items:
                                titulo = item.get("titulo", "")
                                item_id = item.get("id", "")

                                if not titulo:
                                    continue

                                if not self._is_culture_related(f"{titulo} {dept_name}"):
                                    continue

                                item_url = f"{self.base_url}/diario_boe/txt.php?id={item_id}"

                                results.append(RawOpportunity(
                                    title=titulo[:500],
                                    source_url=item_url,
                                    source_name="BOE (API)",
                                    category=self._guess_category(titulo),
                                    discipline="multidisciplinar",
                                    organization=dept_name,
                                    region="Nacional",
                                    description=titulo,
                                    publication_date=date,
                                ))

        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing BOE API response: {e}")

        return results

    def _guess_category(self, title: str) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ["beca", "becas"]):
            return "beca"
        if any(w in title_lower for w in ["subvenci", "ayuda", "ayudas"]):
            return "subvencion"
        if any(w in title_lower for w in ["premio", "concurso"]):
            return "premio"
        if "residencia" in title_lower:
            return "residencia"
        if any(w in title_lower for w in ["empleo", "puesto", "plaza", "oposici"]):
            return "empleo"
        return "convocatoria"

    async def scrape(self) -> list[RawOpportunity]:
        """Fetch BOE summaries for the last 7 days to catch recent entries."""
        results = []
        today = datetime.now()

        for days_ago in range(7):
            date = today - timedelta(days=days_ago)
            # Skip weekends (BOE doesn't publish on weekends)
            if date.weekday() >= 5:
                continue

            day_results = await self._fetch_summary(date)
            results.extend(day_results)

        # Deduplicate
        seen = set()
        unique = []
        for opp in results:
            if opp.source_url not in seen:
                seen.add(opp.source_url)
                unique.append(opp)

        logger.info(f"BOE API: Found {len(unique)} culture-related entries")
        return unique
